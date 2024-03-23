import streamlit as st
from typing import Iterator, Optional
import os
import api
from api import generate_chat_scene_prompt, generate_role_appearance, get_characterglm_response, generate_cogview_image,get_chatglm_response_via_sdk
from data_types import TextMsg, ImageMsg, TextMsgList, MsgList, filter_text_msg
import itertools
import json

# 设置全局属性
st.set_page_config(page_title="Role-Play Generate", page_icon="🤖", layout="wide")

def update_api_key(key:Optional[str] = None):
    api.API_KEY = key

def output_stream_response(response_stream: Iterator[str], placeholder):
    content = ""
    for content in itertools.accumulate(response_stream):
        placeholder.markdown(content)
    return content

def save_Gen_data():
    with open('GenData.json', 'w', encoding='utf-8') as f:
        rets = json.dump(st.session_state['meta'], f, ensure_ascii=False)
        ret = json.dump(st.session_state['history'], f, ensure_ascii=False)
        st.success("数据已保存到GenData.json中")

api_key = st.sidebar.text_input("API_KEY", key="API_kEY", type='password')
update_api_key(api_key)

# 如果没有记录历史状态变量，则初始化一个
if 'history' not in st.session_state:
    st.session_state['history'] = []

def init_session():
    st.session_state['history'] = []

def start_chat(input_placeholder, message_placeholder):
    query=st.chat_input("开始对话吧")
    if not query:
        return
    else:
        input_placeholder.markdown(query)
        st.session_state['history'].append(TextMsg({'role':'user', 'content':query}))
        print(filter_text_msg(st.session_state["history"]))
        response_stream = get_characterglm_response(filter_text_msg(st.session_state["history"]), meta=st.session_state["meta"])
        bot_response = bot_response = output_stream_response(response_stream, message_placeholder)
        if not bot_response:
            message_placeholder.markdown("生成出错")
            st.session_state["history"].pop()
        else:
            st.session_state["history"].append(TextMsg({"role": "assistant", "content": bot_response}))


# 如果没有记录meta状态变量，则初始化一个,meta是一个字典里面包含user_info\bot_info\bot_name\user_name
if 'meta' not in st.session_state:
    st.session_state['meta'] = {
        "user_info": "",
        "bot_info": "",
        "bot_name": "",
        "user_name": ""
    }

egText = '''
那老人独驾轻舟，在墨西哥湾暖流里捕鱼，如今出海已有八十四天，仍是一鱼不获。开始的四十天，有个男孩跟他同去。可是过了四十天还捉不到鱼，那男孩的父母便对他说，那老头子如今不折不扣地成了晦气星，那真是最糟的厄运，于是男孩听了父母的话，到另一条船上去，那条船第一个星期便捕到三尾好鱼。他看见老人每日空船回来，觉得难过，每每下去帮他的忙，或拿绳圈，或拿鱼钩鱼叉，以及卷在桅上的布帆。那帆用面粉袋子补成一块块的，卷起来，就像是一面长败之旗。
老人瘦削而憔悴，颈背皱纹深刻。热带海上阳光的反射引起善性的皮癌，那种褐色的疮疱便长满了两颊，两手时常用索拉扯大鱼，也留下深折的瘢痕。这些瘢痕却都不新，只像无鱼的沙漠里风蚀留痕一样苍老。
除了眼睛，他身上处处都显得苍老。可是他的眼睛跟海水一样颜色，活泼而坚定。
男孩和他爬上了小艇拖靠的海岸，对他说：“桑地雅哥，我又可以跟你一同去了。我们赚了点钱。”
老人曾教男孩捕鱼，男孩因此爱他。
“不行，”老人说，“你跟上了一条好运的船。就跟下去吧。”
“可是别忘了：有一次你一连八十七天没捉到鱼，后来我们连着三个星期，天天都捉到大鱼。”
“我记得，”老人说，“我晓得，你并不是因为不相信我才离开我。”
“是爸爸叫我走的。我是小孩，只好听他的话。”
“我晓得，”老人说，“那是应该的。”
“他不大有信心。”
“自然了，”老人说，“可是我们有信心，对不对？”
“对，”男孩说，“我请你去平台上喝杯啤酒，好不好？喝过了，我们再把这些东西拿回去。”
“好呀，打鱼的还用客气吗！”老人说。
他们坐在平台上，许多渔夫就拿老头子寻开心，可是他并不生气。年纪大些的渔夫只是望着他，觉得难过。
'''

st.title("根据文本生成角色人设")
# 初始化容器
with st.container():
    region1, region2 = st.columns(2)
    with region1:
        st.text("使用实例文本生成角色人设")
        st.markdown(egText)
        gen_picture1 = st.button('生成实例文本角色人设', key = "gen_picture1")
        if gen_picture1:
            instruction = f"""{egText}。根据以上文本生成文本中的角色人设"""
            messages=[
                {
                    "role": "user",
                    "content": instruction.strip()
                }
            ]
            ret = "".join(get_chatglm_response_via_sdk(messages))
            st.write(ret)

    with region2:
        st.text("使用输入文本生成角色人设")
        user_input = st.text_area("输入文本",value = '', height = 300)
        gen_picture2 = st.button('生成输入文本角色人设', key = "gen_picture2")
        if gen_picture2:
            if not user_input:
                st.error('请输入文本')
            else:
                instruction = f"""{user_input}。根据以上文本生成文本中的角色人设"""
                messages=[
                    {
                    "role": "user",
                    "content": instruction.strip()
                    }
                ]
                ret = "".join(get_chatglm_response_via_sdk(messages))
                st.write(ret)

st.title("根据角色设定生成对话")
#初始化一个容器
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        # 创建输入框,标签为 角色名, 输入框名字叫做 bot_name, 当输入框发生变化后 更 session_state中的meta中的bot_name变量
        st.text_input(label="角色名1", key="bot_name", on_change=lambda : st.session_state["meta"].update(bot_name=st.session_state["bot_name"]), help="模型所扮演的角色的名字，不可以为空")
        st.text_area(label="角色1人设", key="bot_info", on_change=lambda : st.session_state["meta"].update(bot_info=st.session_state["bot_info"]), help="角色的详细人设信息，不可以为空")
    with col2:
        st.text_input(label="角色名2",  key="user_name", on_change=lambda : st.session_state["meta"].update(user_name=st.session_state["user_name"]), help="用户的名字，默认为用户")
        st.text_area(label="用户2人设", value="", key="user_info", on_change=lambda : st.session_state["meta"].update(user_info=st.session_state["user_info"]), help="用户的详细人设信息，可以为空")

with st.container():
    butt1, butt2 = st.columns(2)
    with butt1:
        clear_history = st.button("清理历史记录")
        if clear_history:
            init_session()
            st.rerun()
    with butt2:
        save = st.button("保存生成对话到本地")
        if save:
            save_Gen_data()


# 展示对话历史
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

with st.chat_message(name="user", avatar="user"):
    input_placeholder = st.empty()
with st.chat_message(name="assistant", avatar="assistant"):
    message_placeholder = st.empty()

start_chat(input_placeholder, message_placeholder)