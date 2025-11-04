import unittest
from unittest.mock import patch, MagicMock
import os
import gradio as gr

# 在导入app之前设置环境变量
os.environ['PROJECT_ID'] = 'test-project'
os.environ['LOCATION'] = 'global'
os.environ['APP_ID'] = 'test-app'

from app import (
    disable_and_prompt, 
    get_initial_plan_and_update, 
    adjust_plan, 
    prepare_for_final_report,
    generate_final_report,
    finalize_session,
    enable_start_over,
    topic_input,
    plan_btn, 
    report_output, 
    session_state, 
    chat_ui,
    chatbot,
    send_btn,
    finalize_btn,
    new_research_btn,
    msg_input
)

class TestAppFunctions(unittest.TestCase):

    def test_disable_and_prompt(self):
        result = disable_and_prompt()
        self.assertFalse(result[topic_input]['interactive'])
        self.assertFalse(result[plan_btn]['interactive'])
        self.assertEqual(result[report_output], "### 正在生成初步计划，请稍候...")

    @patch('app.call_stream_assist')
    def test_get_initial_plan_and_update(self, mock_call_stream_assist):
        mock_call_stream_assist.return_value = [
            {"answer": {"replies": [{"groundedContent": {"content": {"text": "初步计划内容。"}}}]}},
            {"sessionInfo": {"session": "fake-session-id"}}
        ]
        mock_state = {"session_id": None}
        
        result = get_initial_plan_and_update("test topic", mock_state)

        self.assertFalse(result[topic_input]['interactive'])
        self.assertFalse(result[plan_btn]['interactive'])
        self.assertTrue(result[report_output].startswith("## 研究计划\n\n"))
        self.assertEqual(result[session_state]["session_id"], "fake-session-id")
        self.assertTrue(result[chat_ui]['visible'])

    @patch('builtins.print')
    @patch('app.call_stream_assist')
    def test_adjust_plan(self, mock_call_stream_assist, mock_print):
        mock_call_stream_assist.return_value = [
            {"answer": {"replies": [{"groundedContent": {"content": {"text": "调整后的计划。"}}}]}}
        ]
        mock_state = {"session_id": "fake-session-id"}
        chat_history = []
        generator = adjust_plan("修改意见", chat_history, mock_state)
        results = list(generator)
        self.assertEqual(results[-1], [("修改意见", "调整后的计划。")])

    def test_prepare_for_final_report(self):
        chat_history = [("我的修改意见", "最终计划内容。")]
        result = prepare_for_final_report(chat_history)
        self.assertIn("## 研究计划\n\n最终计划内容。", result[report_output])
        self.assertIn("正在生成最终研究报告，请稍候...", result[report_output])
        self.assertFalse(result[chat_ui]['visible'])
        self.assertFalse(result[finalize_btn]['interactive'])
        self.assertFalse(result[send_btn]['interactive'])

    @patch('app.call_stream_assist')
    def test_generate_final_report(self, mock_call_stream_assist):
        mock_call_stream_assist.return_value = [
            {"answer": {"replies": [{"groundedContent": {"content": {"text": "第一块报告。"}}}]}},
            {"answer": {"replies": [{"groundedContent": {
                "content": {"text": "第二块报告。"}, 
                "textGroundingMetadata": {"references": [
                    {"documentMetadata": {"title": "Test Title", "uri": "http://test.com"}}
                ]}
            }}]}}
        ]
        mock_state = {"session_id": "fake-session-id"}
        report_with_loading = "## 研究计划\n\n最终计划。\n\n---\n### 正在生成最终研究报告，大概**需要15-20分钟**，请稍候..."

        generator = generate_final_report(mock_state, report_with_loading)
        results = list(generator)

        final_report_text = results[-1]
        self.assertIn("## 研究计划\n\n最终计划。", final_report_text)
        self.assertNotIn("大概**需要15-20分钟**", final_report_text)
        self.assertIn("## 最终研究报告", final_report_text)
        self.assertIn("第一块报告。", final_report_text)
        self.assertIn("第二块报告。", final_report_text)
        self.assertTrue(final_report_text.endswith("\n\n"))

    def test_finalize_session(self):
        result = finalize_session()
        self.assertFalse(result[finalize_btn]['visible'])
        self.assertFalse(result[send_btn]['visible'])
        self.assertTrue(result[new_research_btn]['visible'])

    def test_enable_start_over(self):
        result = enable_start_over()
        self.assertTrue(result[topic_input]['interactive'])
        self.assertEqual(result[topic_input]['value'], "")
        self.assertTrue(result[plan_btn]['interactive'])
        self.assertFalse(result[chat_ui]['visible'])
        self.assertEqual(result[report_output], "")
        self.assertIsNone(result[chatbot])
        self.assertEqual(result[msg_input]['value'], "")
        self.assertFalse(result[new_research_btn]['visible'])

if __name__ == '__main__':
    unittest.main()
