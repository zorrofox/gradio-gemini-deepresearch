
import os
from dotenv import load_dotenv
from google.cloud import discoveryengine_v1 as discoveryengine
from google.api_core import exceptions

# 加载 .env 文件中的环境变量
load_dotenv()

def search_documents(project_id, location, data_store_id, search_query):
    """在数据存储中搜索文档。"""
    try:
        client = discoveryengine.SearchServiceClient()

        serving_config = f"projects/{project_id}/locations/{location}/dataStores/{data_store_id}/servingConfigs/default_serving_config"

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=search_query,
            page_size=10,
        )

        response = client.search(request)
        
        results = [result.document for result in response.results]
        return results

    except exceptions.PermissionDenied as e:
        print("权限错误：请确保您的认证凭据正确，并且该服务账号有权访问 Discovery Engine API。")
        print(f"详细信息: {e}")
        return None
    except exceptions.NotFound as e:
        print(f"未找到资源：请检查您的 project_id '{project_id}', location '{location}', 和 data_store_id '{data_store_id}' 是否正确。")
        print(f"详细信息: {e}")
        return None
    except Exception as e:
        print(f"执行搜索时发生未知错误: {e}")
        return None

if __name__ == "__main__":
    # --- 请在此处替换为您的配置 ---
    # 从环境变量加载配置
    PROJECT_ID = os.getenv("PROJECT_ID")
    LOCATION = os.getenv("LOCATION")
    
    # 您需要提供您的数据存储ID
    DATA_STORE_ID = os.getenv("DATA_STORE_ID")  # <--- 从 .env 文件加载
    
    # 您想要执行的搜索查询
    SEARCH_QUERY = "Google"  # <--- 替换为您想搜索的内容

    print(f"项目ID: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"数据存储ID: {DATA_STORE_ID}")
    print(f"搜索查询: \"{SEARCH_QUERY}\"")
    print("---")

    if not all([PROJECT_ID, LOCATION, DATA_STORE_ID]):
        print("错误：请确保 .env 文件中设置了 PROJECT_ID 和 LOCATION, 并且在脚本中设置了 DATA_STORE_ID。")

    else:
        # 执行搜索
        search_results = search_documents(PROJECT_ID, LOCATION, DATA_STORE_ID, SEARCH_QUERY)

        if search_results is not None:
            if search_results:
                print("搜索结果：")
                for i, doc in enumerate(search_results):
                    print(f"--- 结果 {i+1} ---")
                    # 文档对象包含多个字段，这里我们打印一些常用的
                    print(f"  ID: {doc.id}")
                    print(f"  名称: {doc.name}")
                    # 结构化数据 (JSON)
                    if doc.struct_data:
                        print(f"  结构化数据: {doc.struct_data}")
                    # 非结构化数据 (内容)
                    if doc.content and doc.content.uri:
                         print(f"  内容URI: {doc.content.uri}")

            else:
                print("未找到与查询匹配的文档。")
