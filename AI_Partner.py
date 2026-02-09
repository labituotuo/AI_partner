import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json
# 创建OpenAI客户端
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")
#初始化聊天信息
if "message" not in st.session_state:
    st.session_state.message=[]
#初始化昵称
if "name" not in st.session_state:
    st.session_state.name="小甜甜"
#初始化性格
if "character" not in st.session_state:
    st.session_state.character="活泼开朗的东北姑娘"
#会话标识
if "current_session" not in st.session_state:
    st.session_state.current_session=datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#保存会话信息的函数
def save_session():
    # 保存当会话信息
    if st.session_state.current_session:
        # 构建新的会话对象
        session_data = {
            "name": st.session_state.name,
            "character": st.session_state.character,
            "current_session": generate_session_name(),
            "message": st.session_state.message
        }
        # 如果sessions目录不存在，则创建
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        with open(f"sessions/{st.session_state.current_session}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
#生成会话标识
def generate_session_name():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#加载所有会话信息列表
def load_sessions():
    sessions_list=[]
    if os.path.exists("sessions"):
        file_list=os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                sessions_list.append(filename[:-5])
    sessions_list.sort(reverse=True)#排序
    return sessions_list
#加载指定的会话信息
def load_session(session_name):
    if os.path.exists(f"sessions/{session_name}.json"):
        #读取会话信息
        try:
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.message=session_data["message"]
                st.session_state.name=session_data["name"]
                st.session_state.character=session_data["character"]
                st.session_state.current_session=session_name
        except Exception as e:
            print("加载会话失败！", e)
#删除会话信息
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")#删除文件
            #如果删除的当前会话，需要清空当前会话信息
            if session_name==st.session_state.current_session:
                st.session_state.message=[]
                st.session_state.current_session=generate_session_name()
    except Exception as e:
        print("删除会话失败！", e)

#左侧的侧边栏
with st.sidebar:#with：streamlit中的with语句，创建一个上下文管理器，用于管理变量的生命周期。
    st.subheader("AI控制面板")
    #新建会话
    if st.button("新建会话",width="stretch",icon="🥰"):
        # 保存当会话信息
        save_session()
        #创建一个新的会话
        if st.session_state.message:#如果聊天消息非空，则保存当前的会话信息
            st.session_state.message=[]
            st.session_state.current_session=generate_session_name()
            save_session()
            st.rerun()#重新运行当前页面
    #会话历史
    st.text("会话历史")
    session_list=load_sessions()
    for session in session_list:
        col1,col2=st.columns([4,1], vertical_alignment="center")
        with col1:
            #三元运算符：如果条件为真，则返回第一个表达式，否则返回第二个表达式--->语法：值1 if 条件 else 值2
            if st.button(session,width="stretch",key=f"load_{session}",type="primary" if
            session==st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("",width="stretch",icon="❌️",key=f"delete_{session}"):
                delete_session(session)
                st.rerun()
    #分割线
    st.divider()
    st.subheader("伴侣信息")
    name = st.text_input("昵称",placeholder="请输入昵称",value=st.session_state.name)
    if name:
        st.session_state.name=name
    character=st.text_area("性格",placeholder="请输入性格",value=st.session_state.character)
    if character:
        st.session_state.character=character
# 创建页面配置
st.set_page_config(
    page_title="AI_Partner",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)
st.title("小新伴侣智能助手")
st.logo("img.png")
system_prompt="""
    你叫%s，现在是用户的真实伴侣，请完全代入伴侣角色。
        规则：
        每次只回 1 条消息
        禁止任何场景或状态描述性文字
        匹配用户的语言
        回复简短，像微信聊天一样
        有需要的话可以用❤️💖等 emoji 表情
        用符合伴侣性格的方式对话
        回复的内容，要充分体现伴侣的性格特征
    伴侣性格：
        %s
"""
st.text(st.session_state.current_session)#展示会话名称
#展示聊天信息
for message in st.session_state.message:
    if message["role"]=="user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])

prompt=st.chat_input("请输入您要问的问题")
if prompt:#字符串会自动转换为布尔值，非空字符串为True
    st.chat_message("user").write(prompt)
    print("---------------->调用AI大模型，提示词：",prompt)
    #保存用户输入提示词
    st.session_state.message.append({"role": "user", "content": prompt})
    #调用大模型
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt %(st.session_state.name,st.session_state.character)},
            *st.session_state.message
        ],
        stream=True
    )
    #非流式返回结果
    # st.chat_message("assistant").write(response.choices[0].message.content)
    # # 输出大模型返回的结果
    # print("----------------->大模型返回的结果：",response.choices[0].message.content)
    #流式返回结果
    response_message=st.empty()#创建一个空的组件，用于展示大模型返回的结果
    full_response=""
    for chunk in response:
        if chunk.choices[0].delta is not None:
            content=chunk.choices[0].delta.content
            full_response+=content
            response_message.chat_message("assistant").write(full_response)
    # 保存大模型返回的结果
    st.session_state.message.append({"role": "assistant", "content": full_response})
    #保存会话信息
    save_session()