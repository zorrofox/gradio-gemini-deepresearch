import gradio as gr
import requests
import os
import json
import ijson
import gzip
import google.auth
import google.auth.transport.requests
from dotenv import load_dotenv
import traceback

# 在程序开头加载.env文件
load_dotenv()

# 从环境变量中读取配置
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
APP_ID = os.getenv("APP_ID")

# 声明全局组件变量
plan_btn, report_output, session_state, chat_ui = None, None, None, None
chatbot, msg_input, send_btn, finalize_btn, topic_input, new_research_btn = None, None, None, None, None, None

def get_auth_token():
    """通过 google-auth Python SDK 获取认证令牌"""
    try:
        credentials, project = google.auth.default()
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        return {"error": f"使用 google-auth SDK 获取令牌失败: {e}"}

def call_stream_assist(payload):
    """调用 streamAssist API 并处理流式响应的通用函数"""
    token_result = get_auth_token()
    if isinstance(token_result, dict):
        yield {"error": f"错误：无法获取GCP认证令牌。详细错误日志如下：\n---\n{token_result['error']}"}
        return

    headers = {
        'Authorization': f'Bearer {token_result}',
        'Content-Type': 'application/json',
        'X-Goog-User-Project': PROJECT_ID,
    }
    endpoint = f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/engines/{APP_ID}/assistants/default_assistant:streamAssist"
    
    print(f"请求 Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")

    try:
        with requests.post(endpoint, headers=headers, json=payload, stream=True, proxies={'http': '', 'https': ''}) as resp:
            resp.raise_for_status()
            decompressed_stream = gzip.GzipFile(fileobj=resp.raw)
            for obj in ijson.items(decompressed_stream, 'item'):
                print(f"接收到API对象: {obj}")
                yield obj
    except Exception as e:
        print("API调用或解析时出错:")
        traceback.print_exc()
        yield {"error": f"\n\n---\n**处理时发生严重错误:** {e}\n\n详细信息已打印到控制台。"}


with gr.Blocks() as demo:
    gr.Markdown("## Gemini DeepResearch 助理")
    gr.Markdown("输入一个研究主题，系统将流式返回初步的研究计划。您可以在下方的对话框中调整计划。")

    session_state = gr.State(value={"session_id": None})

    with gr.Row():
        topic_input = gr.Textbox(label="研究主题", placeholder="例如：近期关于癌症新药的论文综述")
        plan_btn = gr.Button("生成初步计划")
    
    with gr.Column():
        report_output = gr.Markdown(label="研究进程与报告")

    with gr.Column(visible=False) as chat_ui_instance:
        chat_ui = chat_ui_instance
        gr.Markdown("### 调整研究计划")
        chatbot = gr.Chatbot(label="对话历史")
        with gr.Row():
            msg_input = gr.Textbox(label="输入您的修改意见...", scale=4, interactive=True)
            send_btn = gr.Button("发送修改", scale=1)
        with gr.Row():
            finalize_btn = gr.Button("生成最终报告", variant="primary")

    with gr.Row():
        new_research_btn = gr.Button("开始新的研究", visible=False)

    def disable_and_prompt():
        return {
            topic_input: gr.update(interactive=False),
            plan_btn: gr.update(interactive=False, value="生成中..."),
            report_output: "### 正在生成初步计划，请稍候..."
        }

    def get_initial_plan_and_update(topic, state):
        print("UI: 收到生成初步计划的请求")
        payload = {
            "query": {"text": topic},
            "agentsSpec": {"agentSpecs": {"agentId": "deep_research"}},
            "toolsSpec": {"webGroundingSpec": {}}
        }
        full_text = ""
        final_session_id = None
        for obj in call_stream_assist(payload):
            if "error" in obj:
                full_text += obj["error"]
                break
            
            current_session = obj.get("sessionInfo", {}).get("session")
            if current_session:
                final_session_id = current_session

            answer = obj.get("answer", {})
            if not isinstance(answer, dict): continue

            for reply in answer.get("replies", []):
                if not isinstance(reply, dict): continue
                
                grounded_content = reply.get("groundedContent", {})
                if not isinstance(grounded_content, dict): continue

                content = grounded_content.get("content", {})
                content_text = content.get("text", "") if isinstance(content, dict) else ""
                if content_text and "I don't have enough information to answer" not in content_text:
                    full_text += content_text

                grounding_metadata = grounded_content.get("textGroundingMetadata", {})
                if isinstance(grounding_metadata, dict):
                    references = grounding_metadata.get("references", [])
                    if references:
                        full_text += "\n\n---\n### **引用源：**\n"
                        for i, ref in enumerate(references):
                            doc_meta = ref.get("documentMetadata", {})
                            title = doc_meta.get("title", "N/A")
                            uri = doc_meta.get("uri", "#")
                            full_text += f"{i+1}. [{title}]({uri})\n"

        print(f"UI: 初步计划生成完毕，会话ID: {final_session_id}")
        state["session_id"] = final_session_id
        full_text_with_header = "## 研究计划\n\n" + full_text
        return {
            topic_input: gr.update(interactive=False),
            plan_btn: gr.update(interactive=False),
            report_output: full_text_with_header,
            session_state: state,
            chat_ui: gr.update(visible=True)
        }

    def adjust_plan(message, chat_history, state):
        print(f"UI: 收到调整计划的请求: {message}")
        if not state["session_id"]:
            chat_history.append((message, "错误：会话ID不存在，请先生成初步计划。"))
            yield chat_history
            return

        payload = {
            "query": {"text": message},
            "session": state["session_id"],
            "agentsSpec": {"agentSpecs": {"agentId": "deep_research"}}
        }
        print(f"调整计划请求 Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        bot_message = ""
        chat_history.append((message, bot_message))
        for obj in call_stream_assist(payload):
            if "error" in obj:
                bot_message += obj["error"]
                chat_history[-1] = (message, bot_message)
                yield chat_history
                break

            answer = obj.get("answer", {})
            if not isinstance(answer, dict): continue

            for reply in answer.get("replies", []):
                if not isinstance(reply, dict): continue
                
                grounded_content = reply.get("groundedContent", {})
                if not isinstance(grounded_content, dict): continue

                content = grounded_content.get("content", {})
                content_text = content.get("text", "") if isinstance(content, dict) else ""
                if content_text:
                    bot_message += content_text
                    chat_history[-1] = (message, bot_message)
                    yield chat_history
        print("UI: 计划调整完毕")

    def prepare_for_final_report(chat_history):
        print("UI: 准备生成最终报告...")
        final_plan = chat_history[-1][1] if chat_history else ""
        final_plan_with_header = "## 研究计划\n\n" + final_plan
        loading_text = final_plan_with_header + "\n\n---\n### 正在生成最终研究报告，请稍候..."
        return {
            report_output: loading_text,
            chat_ui: gr.update(visible=False),
            finalize_btn: gr.update(interactive=False, value="生成中..."),
            send_btn: gr.update(interactive=False)
        }

    def generate_final_report(state, report_with_loading_text):
        print("UI: 收到生成最终报告的请求")
        if not state["session_id"]:
            yield report_with_loading_text + "\n\n**错误：会话ID不存在，请先生成初步计划。**"
            return

        payload = {
            "query": {"text": "Start Research"},
            "session": state["session_id"],
            "agentsSpec": {"agentSpecs": {"agentId": "deep_research"}}
        }
        
        separator = "\n\n---\n### 正在生成最终研究报告，大概**需要15-20分钟**，请稍候..."
        final_plan_with_header = report_with_loading_text.split(separator)[0]

        is_first_chunk = True
        full_report_content = ""

        for obj in call_stream_assist(payload):
            if "error" in obj:
                full_report_content = final_plan_with_header + "\n\n" + obj["error"]
                yield full_report_content
                break

            answer = obj.get("answer", {})
            if not isinstance(answer, dict): continue

            for reply in answer.get("replies", []):
                if not isinstance(reply, dict): continue
                
                grounded_content = reply.get("groundedContent", {})
                if not isinstance(grounded_content, dict): continue

                content = grounded_content.get("content", {})
                content_text = content.get("text", "") if isinstance(content, dict) else ""
                
                if content_text:
                    if is_first_chunk:
                        full_report_content = final_plan_with_header + "\n\n---\n## 最终研究报告\n\n" + content_text
                        is_first_chunk = False
                    else:
                        full_report_content += content_text

                grounding_metadata = grounded_content.get("textGroundingMetadata", {})
                if isinstance(grounding_metadata, dict):
                    references = grounding_metadata.get("references", [])
                    if references:
                        full_report_content += "\n\n---\n### **引用源：**\n"
                        for i, ref in enumerate(references):
                            doc_meta = ref.get("documentMetadata", {})
                            title = doc_meta.get("title", "N/A")
                            uri = doc_meta.get("uri", "#")
                            full_report_content += f"{i+1}. [{title}]({uri})\n"
                        full_report_content += "\n\n"
            if full_report_content:
                yield full_report_content
        print("UI: 最终报告生成完毕")

    def finalize_session():
        print("UI: 会话结束，显示‘开始新的研究’按钮")
        return {
            finalize_btn: gr.update(visible=False),
            send_btn: gr.update(visible=False),
            new_research_btn: gr.update(visible=True)
        }

    def enable_start_over():
        print("UI: 重置所有控件，开始新的研究")
        return {
            topic_input: gr.update(interactive=True, value=""),
            plan_btn: gr.update(interactive=True, value="生成初步计划"),
            chat_ui: gr.update(visible=False),
            report_output: "",
            chatbot: None,
            msg_input: gr.update(value=""),
            new_research_btn: gr.update(visible=False)
        }

    plan_btn.click(
        fn=disable_and_prompt,
        inputs=None,
        outputs=[topic_input, plan_btn, report_output]
    ).then(
        fn=get_initial_plan_and_update,
        inputs=[topic_input, session_state],
        outputs=[topic_input, plan_btn, report_output, session_state, chat_ui]
    )
    
    send_btn.click(
        fn=adjust_plan,
        inputs=[msg_input, chatbot, session_state],
        outputs=[chatbot]
    ).then(lambda: gr.update(value=""), None, [msg_input], queue=False)

    finalize_btn.click(
        fn=prepare_for_final_report,
        inputs=[chatbot],
        outputs=[report_output, chat_ui, finalize_btn, send_btn]
    ).then(
        fn=generate_final_report,
        inputs=[session_state, report_output],
        outputs=[report_output]
    ).then(
        fn=finalize_session,
        inputs=None,
        outputs=[finalize_btn, send_btn, new_research_btn]
    )

    new_research_btn.click(
        fn=enable_start_over,
        inputs=None,
        outputs=[topic_input, plan_btn, chat_ui, report_output, chatbot, msg_input, new_research_btn]
    )

if __name__ == "__main__":
    demo.launch(server_port=7888)