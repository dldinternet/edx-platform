"""
Python tests for the Survey views
"""

import json
from collections import OrderedDict

from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from survey.models import SurveyForm

from xmodule.modulestore.tests.factories import CourseFactory


class SurveyViewsTests(TestCase):
    """
    All tests for the views.py file
    """
    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        self.client = Client()

        # Create two accounts
        self.password = 'abc'
        self.student = User.objects.create_user('student', 'student@test.com', self.password)

        self.test_survey_name = 'TestSurvey'
        self.test_form = '<input name="field1" /><input name="field2" /><select name="ddl"><option>1</option></select>'

        self.student_answers = OrderedDict({
            u'field1': u'value1',
            u'field2': u'value2',
            u'ddl': u'1',
        })

        self.course = CourseFactory.create(
            course_survey_required=True,
            course_survey_name=self.test_survey_name
        )

        self.survey = SurveyForm.create(self.test_survey_name, self.test_form)

        self.view_url = reverse('view_survey', args=[self.test_survey_name])
        self.postback_url = reverse('submit_answers', args=[self.test_survey_name])

        self.client.login(username=self.student.username, password=self.password)

    def test_unauthenticated_survey_view(self):
        """
        Asserts that an unauthenticated user cannot access a survey
        """
        anon_user = Client()

        resp = anon_user.get(self.view_url)
        self.assertEquals(resp.status_code, 302)

    def test_survey_not_found(self):
        """
        Asserts that if we ask for a Survey that does not exist, then we get a 302 redirect
        """
        resp = self.client.get(reverse('view_survey', args=['NonExisting']))
        self.assertEquals(resp.status_code, 302)

    def test_authenticated_survey_view(self):
        """
        Asserts that an authenticated user can see the survey
        """
        resp = self.client.get(self.view_url)
        self.assertEquals(resp.status_code, 200)

        # is the SurveyForm html present in the HTML response?
        self.assertIn(self.test_form, resp.content)

    def test_unautneticated_survey_postback(self):
        """
        Asserts that an anonymous user cannot answer a survey
        """
        anon_user = Client()
        resp = anon_user.post(
            self.postback_url,
            self.student_answers
        )
        self.assertEquals(resp.status_code, 302)

    def test_survey_postback_to_nonexisting_survey(self):
        """
        Asserts that any attempts to post back to a non existing survey returns a 404
        """
        resp = self.client.post(
            reverse('submit_answers', args=['NonExisting']),
            self.student_answers
        )
        self.assertEquals(resp.status_code, 404)

    def test_survey_postback(self):
        """
        Asserts that a well formed postback of survey answers is properly stored in the
        database
        """
        resp = self.client.post(
            self.postback_url,
            self.student_answers
        )
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('redirect_url', data)

        answers = self.survey.get_answers(self.student)
        self.assertEquals(answers[self.student.id], self.student_answers)

    def test_strip_extra_fields(self):
        """
        Verify that any not expected field name in the post-back is not stored
        in the database
        """
        data = dict.copy(self.student_answers)

        data['csrfmiddlewaretoken'] = 'foo'
        data['_redirect_url'] = 'bar'

        resp = self.client.post(
            self.postback_url,
            data
        )
        self.assertEquals(resp.status_code, 200)
        answers = self.survey.get_answers(self.student)
        self.assertNotIn('csrfmiddlewaretoken', answers[self.student.id])
        self.assertNotIn('_redirect_url', answers[self.student.id])

    def test_encoding_answers(self):
        """
        Verify that if some potentially harmful input data is sent, that is is properly HTML encoded
        """
        data = dict.copy(self.student_answers)

        data['field1'] = '<script type="javascript">alert("Deleting filesystem...")</script>'

        resp = self.client.post(
            self.postback_url,
            data
        )
        self.assertEquals(resp.status_code, 200)
        answers = self.survey.get_answers(self.student)
        self.assertEqual(
            '&lt;script type=&quot;javascript&quot;&gt;alert(&quot;Deleting filesystem...&quot;)&lt;/script&gt;',
            answers[self.student.id]['field1']
        )
