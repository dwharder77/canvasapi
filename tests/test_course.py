import unittest
import uuid
import os

import requests_mock

from pycanvas import Canvas
from pycanvas.assignment import Assignment
from pycanvas.course import Course, CourseNickname, Page
from pycanvas.discussion_topic import DiscussionTopic
from pycanvas.enrollment import Enrollment
from pycanvas.exceptions import ResourceDoesNotExist, RequiredFieldMissing
from pycanvas.external_tool import ExternalTool
from pycanvas.group import Group, GroupCategory
from pycanvas.module import Module
from pycanvas.quiz import Quiz
from pycanvas.section import Section
from pycanvas.user import User
from tests import settings
from tests.util import register_uris


@requests_mock.Mocker()
class TestCourse(unittest.TestCase):

    @classmethod
    def setUp(self):
        self.canvas = Canvas(settings.BASE_URL, settings.API_KEY)

        with requests_mock.Mocker() as m:
            requires = {
                'course': ['get_by_id', 'get_page'],
                'quiz': ['get_by_id'],
                'user': ['get_by_id']
            }
            register_uris(requires, m)

            self.course = self.canvas.get_course(1)
            self.page = self.course.get_page('my-url')
            self.quiz = self.course.get_quiz(1)
            self.user = self.canvas.get_user(1)

    # __str__()
    def test__str__(self, m):
        string = str(self.course)
        assert isinstance(string, str)

    # conclude()
    def test_conclude(self, m):
        register_uris({'course': ['conclude']}, m)

        success = self.course.conclude()
        assert success

    # delete()
    def test_delete(self, m):
        register_uris({'course': ['delete']}, m)

        success = self.course.delete()
        assert success

    # update()
    def test_update(self, m):
        register_uris({'course': ['update']}, m)

        new_name = 'New Name'
        self.course.update(course={'name': new_name})
        assert self.course.name == new_name

    # get_user()
    def test_get_user(self, m):
        register_uris({'course': ['get_user']}, m)

        user = self.course.get_user(1)

        assert isinstance(user, User)
        assert hasattr(user, 'name')

    def test_get_user_id_type(self, m):
        register_uris({'course': ['get_user_id_type']}, m)

        user = self.course.get_user("SISLOGIN", "sis_login_id")

        assert isinstance(user, User)
        assert hasattr(user, 'name')

    # get_users()
    def test_get_users(self, m):
        register_uris({'course': ['get_users', 'get_users_p2']}, m)

        users = self.course.get_users()
        user_list = [user for user in users]

        assert len(user_list) == 4
        assert isinstance(user_list[0], User)

    # enroll_user()
    def test_enroll_user(self, m):
        requires = {
            'course': ['enroll_user'],
            'user': ['get_by_id']
        }
        register_uris(requires, m)

        enrollment_type = 'TeacherEnrollment'
        user = self.canvas.get_user(1)
        enrollment = self.course.enroll_user(user, enrollment_type)

        assert isinstance(enrollment, Enrollment)
        assert hasattr(enrollment, 'type')
        assert enrollment.type == enrollment_type

    # get_recent_students()
    def test_get_recent_students(self, m):
        recent = {'course': ['get_recent_students', 'get_recent_students_p2']}
        register_uris(recent, m)

        students = self.course.get_recent_students()
        student_list = [student for student in students]

        assert len(student_list) == 4
        assert isinstance(student_list[0], User)
        assert hasattr(student_list[0], 'name')

    # preview_html()
    def test_preview_html(self, m):
        register_uris({'course': ['preview_html']}, m)

        html_str = "<script></script><p>hello</p>"
        prev_html = self.course.preview_html(html_str)

        assert isinstance(prev_html, (str, unicode))
        assert prev_html == "<p>hello</p>"

    # get_settings()
    def test_get_settings(self, m):
        register_uris({'course': ['settings']}, m)

        settings = self.course.get_settings()

        assert isinstance(settings, dict)

    # update_settings()
    def test_update_settings(self, m):
        register_uris({'course': ['update_settings']}, m)

        settings = self.course.update_settings()

        assert isinstance(settings, dict)
        assert settings['hide_final_grades'] is True

    # upload()
    def test_upload(self, m):
        register_uris({'course': ['upload', 'upload_final']}, m)

        filename = 'testfile_%s' % uuid.uuid4().hex
        file = open(filename, 'w+')

        response = self.course.upload(file)

        assert response[0] is True
        assert isinstance(response[1], dict)
        assert 'url' in response[1]

        # http://stackoverflow.com/a/10840586
        # Not as stupid as it looks.
        try:
            os.remove(filename)
        except OSError:
            pass

    # reset()
    def test_reset(self, m):
        register_uris({'course': ['reset']}, m)

        course = self.course.reset()

        assert isinstance(course, Course)
        assert hasattr(course, 'name')

    # create_quiz()
    def test_create_quiz(self, m):
        register_uris({'course': ['create_quiz']}, m)

        title = 'Newer Title'
        new_quiz = self.course.create_quiz({'title': title})

        assert isinstance(new_quiz, Quiz)
        assert hasattr(new_quiz, 'title')
        assert new_quiz.title == title
        assert hasattr(new_quiz, 'course_id')
        assert new_quiz.course_id == self.course.id

    def test_create_quiz_fail(self, m):
        with self.assertRaises(RequiredFieldMissing):
            self.course.create_quiz({})

    # get_quiz()
    def test_get_quiz(self, m):
        register_uris({'course': ['get_quiz']}, m)

        target_quiz = self.course.get_quiz(1)

        assert isinstance(target_quiz, Quiz)
        assert hasattr(target_quiz, 'course_id')
        assert target_quiz.course_id == self.course.id

    def test_get_quiz_fail(self, m):
        register_uris({'generic': ['not_found']}, m)

        with self.assertRaises(ResourceDoesNotExist):
            self.course.get_quiz(settings.INVALID_ID)

    # get_quizzes()
    def test_get_quizzes(self, m):
        register_uris({'course': ['list_quizzes', 'list_quizzes2']}, m)

        quizzes = self.course.get_quizzes()
        quiz_list = [quiz for quiz in quizzes]

        assert len(quiz_list) == 4
        assert isinstance(quiz_list[0], Quiz)
        assert hasattr(quiz_list[0], 'course_id')
        assert quiz_list[0].course_id == self.course.id

    # get_modules()
    def test_get_modules(self, m):
        register_uris({'course': ['list_modules', 'list_modules2']}, m)

        modules = self.course.get_modules()
        module_list = [module for module in modules]

        assert len(module_list) == 4
        assert isinstance(module_list[0], Module)
        assert hasattr(module_list[0], 'course_id')
        assert module_list[0].course_id == self.course.id

    # get_module()
    def test_get_module(self, m):
        register_uris({'course': ['get_module_by_id']}, m)

        target_module = self.course.get_module(1)

        assert isinstance(target_module, Module)
        assert hasattr(target_module, 'course_id')
        assert target_module.course_id == self.course.id

    # create_module()
    def test_create_module(self, m):
        register_uris({'course': ['create_module']}, m)

        name = 'Name'
        new_module = self.course.create_module(module={'name': name})

        assert isinstance(new_module, Module)
        assert hasattr(new_module, 'name')
        assert hasattr(new_module, 'course_id')
        assert new_module.course_id == self.course.id

    def test_create_module_fail(self, m):
        with self.assertRaises(RequiredFieldMissing):
            self.course.create_module(module={})

    # get_enrollments()
    def test_get_enrollments(self, m):
        register_uris({'course': ['list_enrollments', 'list_enrollments_2']}, m)

        enrollments = self.course.get_enrollments()
        enrollment_list = [enrollment for enrollment in enrollments]

        assert len(enrollment_list) == 4
        assert isinstance(enrollment_list[0], Enrollment)

    # get_section
    def test_get_section(self, m):
        register_uris({'course': ['get_section']}, m)

        section = self.course.get_section(1)

        assert isinstance(section, Section)

    # create_assignment()
    def test_create_assignment(self, m):
        register_uris({'course': ['create_assignment']}, m)

        name = 'Newly Created Assignment'

        assignment = self.course.create_assignment(assignment={'name': name})

        assert isinstance(assignment, Assignment)
        assert hasattr(assignment, 'name')
        assert assignment.name == name
        assert assignment.id == 5

    def test_create_assignment_fail(self, m):
        with self.assertRaises(RequiredFieldMissing):
            self.course.create_assignment(assignment={})

    # get_assignment()
    def test_get_assignment(self, m):
        register_uris({'course': ['get_assignment_by_id']}, m)

        assignment = self.course.get_assignment('5')

        assert isinstance(assignment, Assignment)
        assert hasattr(assignment, 'name')

    # get_assignments()
    def test_get_assignments(self, m):
        requires = {'course': ['get_all_assignments', 'get_all_assignments2']}
        register_uris(requires, m)

        assignments = self.course.get_assignments()
        assignment_list = [assignment for assignment in assignments]

        assert isinstance(assignments[0], Assignment)
        assert len(assignment_list) == 4

    # show_front_page()
    def test_show_front_page(self, m):
        register_uris({'course': ['show_front_page']}, m)

        front_page = self.course.show_front_page()

        assert isinstance(front_page, Page)
        assert hasattr(front_page, 'url')
        assert hasattr(front_page, 'title')

    # create_front_page()
    def test_edit_front_page(self, m):
        register_uris({'course': ['edit_front_page']}, m)

        new_front_page = self.course.edit_front_page()

        assert isinstance(new_front_page, Page)
        assert hasattr(new_front_page, 'url')
        assert hasattr(new_front_page, 'title')

    # get_page()
    def test_get_page(self, m):
        register_uris({'course': ['get_page']}, m)

        url = 'my-url'
        page = self.course.get_page(url)

        assert isinstance(page, Page)

    # get_pages()
    def test_get_pages(self, m):
        register_uris({'course': ['get_pages', 'get_pages2']}, m)

        pages = self.course.get_pages()
        page_list = [page for page in pages]

        assert len(page_list) == 4
        assert isinstance(page_list[0], Page)
        assert hasattr(page_list[0], 'course_id')
        assert page_list[0].course_id == self.course.id

    # create_page()
    def test_create_page(self, m):
        register_uris({'course': ['create_page']}, m)

        title = "Newest Page"
        new_page = self.course.create_page(wiki_page={'title': title})

        assert isinstance(new_page, Page)
        assert hasattr(new_page, 'title')
        assert new_page.title == title
        assert hasattr(new_page, 'course_id')
        assert new_page.course_id == self.course.id

    def test_create_page_fail(self, m):
        with self.assertRaises(RequiredFieldMissing):
            self.course.create_page(settings.INVALID_ID)

    # get_external_tool()
    def test_get_external_tool(self, m):
        register_uris({'external_tool': ['get_by_id_course']}, m)

        tool = self.course.get_external_tool(1)

        assert isinstance(tool, ExternalTool)
        assert hasattr(tool, 'name')

    # get_external_tools()
    def test_get_external_tools(self, m):
        requires = {'course': ['get_external_tools', 'get_external_tools_p2']}
        register_uris(requires, m)

        tools = self.course.get_external_tools()
        tool_list = [tool for tool in tools]

        assert isinstance(tool_list[0], ExternalTool)
        assert len(tool_list) == 4

    def test_list_sections(self, m):
        register_uris({'course': ['list_sections', 'list_sections2']}, m)

        sections = self.course.list_sections()
        section_list = [sect for sect in sections]

        assert isinstance(section_list[0], Section)
        assert len(section_list) == 4

    def test_create_course_section(self, m):
        register_uris({'course': ['create_section']}, m)

        section = self.course.create_course_section()

        assert isinstance(section, Section)

    def test_list_groups(self, m):
        requires = {'course': ['list_groups_context', 'list_groups_context2']}
        register_uris(requires, m)

        groups = self.course.list_groups()
        group_list = [group for group in groups]

        assert isinstance(group_list[0], Group)
        assert len(group_list) == 4

    # create_group_category()
    def test_create_group_category(self, m):
        register_uris({'course': ['create_group_category']}, m)

        name_str = "Test String"
        response = self.course.create_group_category(name=name_str)
        assert isinstance(response, GroupCategory)

    # list_group_categories()
    def test_list_group_categories(self, m):
        register_uris({'course': ['list_group_categories']}, m)

        response = self.course.list_group_categories()
        category_list = [category for category in response]
        assert isinstance(category_list[0], GroupCategory)

    # get_discussion_topic()
    def test_get_discussion_topic(self, m):
        register_uris({'course': ['get_discussion_topic']}, m)

        topic_id = 1
        discussion = self.course.get_discussion_topic(topic_id)
        self.assertIsInstance(discussion, DiscussionTopic)
        assert hasattr(discussion, 'course_id')
        self.assertEquals(discussion.course_id, 1)

    # get_discussion_topics()
    def test_get_discussion_topics(self, m):
        register_uris({'course': ['get_discussion_topics']}, m)

        response = self.course.get_discussion_topics()
        discussion_list = [discussion for discussion in response]
        self.assertIsInstance(discussion_list[0], DiscussionTopic)
        assert hasattr(discussion_list[0], 'course_id')
        self.assertEquals(2, len(discussion_list))

    # create_discussion_topic()
    def test_create_discussion_topic(self, m):
        register_uris({'course': ['create_discussion_topic']}, m)

        title = "Topic 1"
        discussion = self.course.create_discussion_topic()
        self.assertIsInstance(discussion, DiscussionTopic)
        assert hasattr(discussion, 'course_id')
        self.assertEquals(title, discussion.title)
        self.assertEquals(discussion.course_id, 1)

    # update_discussion_topic()
    def test_update_discussion_topic(self, m):
        register_uris({'course': ['update_discussion_topic']}, m)

        topic_id = 1
        discussion = self.course.update_discussion_topic(topic_id)
        self.assertIsInstance(discussion, DiscussionTopic)
        assert hasattr(discussion, 'course_id')
        self.assertEquals(topic_id, discussion.id)
        self.assertEquals(discussion.course_id, 1)

    def test_reorder_pinned_topics(self, m):
        register_uris({'course': ['reorder_pinned_topics']}, m)

        order = 1, 2

        discussions = self.course.reorder_pinned_topics(order=order)
        discussion_list = [discussion for discussion in discussions]
        self.assertIsInstance(discussion_list[0], DiscussionTopic)
        assert hasattr(discussion_list[0], 'course_id')
        self.assertEquals(2, len(discussion_list))

@requests_mock.Mocker()
class TestCourseNickname(unittest.TestCase):

    @classmethod
    def setUp(self):
        self.canvas = Canvas(settings.BASE_URL, settings.API_KEY)

        with requests_mock.Mocker() as m:
            register_uris({'user': ['course_nickname']}, m)
            self.nickname = self.canvas.get_course_nickname(1)

    # __str__()
    def test__str__(self, m):
        string = str(self.nickname)
        assert isinstance(string, str)

    # remove()
    def test_remove(self, m):
        register_uris({'user': ['remove_nickname']}, m)

        deleted_nick = self.nickname.remove()

        assert isinstance(deleted_nick, CourseNickname)
        assert hasattr(deleted_nick, 'nickname')
