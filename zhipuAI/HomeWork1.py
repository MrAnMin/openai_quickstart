import os
from typing import Iterator, Optional
import itertools

import streamlit as st
import api

from api import generate_chat_scene_prompt, generate_role_appearance, get_characterglm_response, generate_cogview_image
from data_types import TextMsg, ImageMsg, TextMsgList, MsgList, filter_text_msg

def verify_meta() -> bool:
    # 检查`角色名`和`角色人设`是否空，若为空，则弹出提醒
    if st.session_state["meta"]["bot_name"] == "" or st.session_state["meta"]["bot_info"] == "":
        st.error("角色名和角色人设不能为空")
        return False
    else:
        return True

def output_stream_response(response_stream: Iterator[str], placeholder):
    content = ""
    for content in itertools.accumulate(response_stream):
        placeholder.markdown(content)
    return content

def start_chat():
    query=st.chat_input("开始对话吧")
    print(query)
    if not query:
        return
    # 如果发送了
    else:
        # `角色名`和`角色人设`是否空,若为空，则弹出提醒
        if not verify_meta():
            return 
        # 如果没有api_key，弹出提示框
        if not api.API_KEY:
            st.error("未设置API_KEY")
        # input_placeholder.markdown(query)
        st.session_state['history'].append(TextMsg({'role':'user', 'content':query}))
        response_stream = get_characterglm_response(filter_text_msg(st.session_state["history"]), meta=st.session_state["meta"])
        bot_response = output_stream_response(response_stream, message_placeholder)
        #如果生成错错，把保留的历史数据弹出
        if not bot_response:
            message_placeholder.markdown("生成出错")
            st.session_state["history"].pop()
        else:
            st.session_state["history"].append(TextMsg({"role": "assistant", "content": bot_response}))

def draw_new_image(imagestyle):
    """生成一张图片，并展示在页面上"""
    if not verify_meta():
        return
    text_messages = filter_text_msg(st.session_state["history"])
    if text_messages:
        # 若有对话历史，则结合角色人设和对话历史生成图片
        image_prompt = "".join(
            generate_chat_scene_prompt(
                text_messages[-10: ],
                meta=st.session_state["meta"]
            )
        )
    else:
        # 若没有对话历史，则根据角色人设生成图片
        image_prompt = "".join(generate_role_appearance(st.session_state["meta"]["bot_info"]))
    
    if not image_prompt:
        st.error("调用chatglm生成Cogview prompt出错")
        return
    
    # TODO: 加上风格选项
    # image_prompt = '二次元风格。' + image_prompt.strip()
    image_prompt = f'{imagestyle}风格。' + image_prompt.strip()
    
    print(f"image_prompt = {image_prompt}")
    n_retry = 3
    st.markdown("正在生成图片，请稍等...")
    for i in range(n_retry):
        try:
            img_url = generate_cogview_image(image_prompt)
        except Exception as e:
            if i < n_retry - 1:
                st.error("遇到了一点小问题，重试中...")
            else:
                st.error("又失败啦，点击【生成图片】按钮可再次重试")
                return
        else:
            break
    img_msg = ImageMsg({"role": "image", "image": img_url, "caption": image_prompt})
    # 若history的末尾有图片消息，则替换它，（重新生成）
    # 否则，append（新增）
    while st.session_state["history"] and st.session_state["history"][-1]["role"] == "image":
        st.session_state["history"].pop()
    st.session_state["history"].append(img_msg)
    st.rerun()


# 设置全局属性
st.set_page_config(page_title="CharacterGLM API Demo", page_icon="🤖", layout="wide")
# 获取环境变量键的值，否则返回默认值，如果有则判断是否为 '1', 'yes', 'y', 'true', 't', 'on'
# 判断是否开启了DEBUG模式
debug = os.getenv("DEBUG", '').lower() in ('1', 'yes', 'y', 'true', 't', 'on')

def update_api_key(key:Optional[str] = None):
    '''
    更新api_key
    '''
    # 如果开启了debug
    # if debug:
    #     print(f'update_api_key. st.session_state["API_KEY"] = {st.session_state["API_KEY"]}, key = {key}')
    # key = key or st.session_state['API_KEY']
    if key:
        api.API_KEY = key

# 创建一个侧边栏，侧边栏中有一个文本输入框组件，输入框旁边的标签为API_KEY
# 初始值为系统中的API_KEY环境变量的值,组件的名字叫做API_kEY，数据类型是password
api_key = st.sidebar.text_input("API_KEY", value=os.getenv("API_KEY", ''), key="API_kEY", type='password',on_change=update_api_key)
update_api_key(api_key)

#初始化状态变量
# 如果没有记录历史状态变量，则初始化一个
if 'history' not in st.session_state:
    st.session_state['history'] = []
# 如果没有记录meta状态变量，则初始化一个,meta是一个字典里面包含user_info\bot_info\bot_name\user_name
if 'meta' not in st.session_state:
    st.session_state['meta'] = {
        "user_info": "",
        "bot_info": "",
        "bot_name": "",
        "user_name": ""
    }

def init_session():
    '''
    初始化st.session_state['history'] 
    '''
    st.session_state['history'] = []

# # 初始化4个输入框的名字
# meta_labels = {
#     "bot_name": "角色名",
#     "user_name": "用户名", 
#     "bot_info": "角色人设",
#     "user_info": "用户人设"
# }
# 初始化页面布局,创建一个容器
with st.container():
    # 创建两列布局
    col1, col2 = st.columns(2)
    with col1:
        # 创建输入框,标签为 角色名, 输入框名字叫做 bot_name, 当输入框发生变化后 更 session_state中的meta中的bot_name变量
        st.text_input(label="角色名", key="bot_name", on_change=lambda : st.session_state["meta"].update(bot_name=st.session_state["bot_name"]), help="模型所扮演的角色的名字，不可以为空")
        st.text_area(label="角色人设", key="bot_info", on_change=lambda : st.session_state["meta"].update(bot_info=st.session_state["bot_info"]), help="角色的详细人设信息，不可以为空")
    with col2:
        st.text_input(label="用户名", value="用户", key="user_name", on_change=lambda : st.session_state["meta"].update(user_name=st.session_state["user_name"]), help="用户的名字，默认为用户")
        st.text_area(label="用户人设", value="", key="user_info", on_change=lambda : st.session_state["meta"].update(user_info=st.session_state["user_info"]), help="用户的详细人设信息，可以为空")

#初始化button的名字
button_labels = {
    "clear_meta": "清空人设",
    "clear_history": "清空对话历史",
}
if debug:
    button_labels.update({
        "show_api_key": "查看API_KEY",
        "show_meta": "查看meta",
        "show_history": "查看历史"
    })

# 初始化一个容器
with st.container():
    # 计算button个数
    n_button = len(button_labels)
    # 初始化n_button个列
    cols = st.columns(n_button)
    # 设置n_button个button 对应为clear_meta:cols[0] clear_history:cols[1]....
    button_key_to_col = dict(zip(button_labels.keys(), cols))
    # 初始化清空人设button名字叫做
    with button_key_to_col['clear_meta']:
        clear_meta = st.button(button_labels['clear_meta'],key = 'clear_meta')
        # 当clear_meta被点击，则st.session_state中的meta标志重新初始化
        if clear_meta:
            st.session_state['meta'] = {
                "user_info": "",
                "bot_info": "",
                "bot_name": "",
                "user_name": ""
            }
            # 重新执行当前streamlit应用
            st.rerun()
    # 初始化清空对话历史button名字叫做 clear_history  
    with button_key_to_col["clear_history"]:
        clear_history = st.button(button_labels["clear_history"], key="clear_history")
        # 当clear_meta被点击，则st.session_state中的 history 标志重新初始化
        if clear_history:
            init_session()
            st.rerun()

        
    # 如果开启debug模式
    if debug:
        with button_key_to_col["show_api_key"]:
            show_api_key = st.button(button_labels["show_api_key"], key="show_api_key")
            if show_api_key:
                print(f"API_KEY = {api.API_KEY}")
        
        with button_key_to_col["show_meta"]:
            show_meta = st.button(button_labels["show_meta"], key="show_meta")
            if show_meta:
                print(f"meta = {st.session_state['meta']}")
        
        with button_key_to_col["show_history"]:
            show_history = st.button(button_labels["show_history"], key="show_history")
            if show_history:
                print(f"history = {st.session_state['history']}")

# 初始化一个容器
options = ['写实', '二次元', '迪士尼','山水画','中国风', '超现实主义']
with st.container():
    col_1, col_2 = st.columns(2)
    with col_1:
        # 创建下拉菜单
        selection = st.selectbox('设置风格',  options, index=0, key ='select_style')
    with col_2:
            # 点击生成图片，出发后调用生成图片函数  
        # with button_key_to_col["gen_picture"]:
        gen_picture = st.button('生成图片', key="gen_picture")
    

# # 展示对话历史
for msg in st.session_state["history"]:
    if msg["role"] == "user":
        with st.chat_message(name="user", avatar="user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.markdown(msg["content"])
    elif msg["role"] == "image":
        with st.chat_message(name="assistant", avatar="assistant"):
            st.image(msg["image"], caption=msg.get("caption", None))
    else:
        raise Exception("Invalid role")

if gen_picture:
    draw_new_image(selection)

with st.chat_message(name="user", avatar="user"):
    input_placeholder = st.empty()
with st.chat_message(name="assistant", avatar="assistant"):
    message_placeholder = st.empty()


start_chat()