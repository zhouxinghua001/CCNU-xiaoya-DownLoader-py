import os
import re
from typing import Any, TextIO

import requests


def get_json(url: str, headers: dict) -> bool | dict:
    try:
        response = requests.get(url=url, headers=headers)
        return response.json()
    except:
        return False


def get_course(headers: dict) -> tuple[list[Any], list[Any]]:
    url = "https://ccnu.ai-augmented.com/api/jx-iresource/group/student/groups?time_flag=1"
    data = get_json(url=url, headers=headers).get("data")
    return [i.get("name") for i in data], [i.get("id") for i in data]


def choose(name_list: list, id_list: list) -> None:
    for i in range(len(name_list)):
        print(f"{i}.{name_list[i]}")
    temp = int(input("请输入你要爬取的课程编号"))
    while temp not in range(len(name_list)):
        print("输入有误")
        temp = int(input("请输入你要爬取的课程编号"))
    url = ("https://ccnu.ai-augmented.com/api/jx-iresource/resource/queryCourseResources?group_id=" + id_list[temp])
    download_yes = input("将下载可下载的视频资源，是否下载(Y/n):")
    if download_yes == "N" or download_yes == "n":
        video = False
    else:
        video = True
    log = make_root(course_id=id_list[temp])
    html = get_json(url=url, headers=headers)
    file_list = data2list(data=html)
    tree = list2tree(file_list=file_list)
    makedir_and_download(file_tree=tree, headers=headers, video=video, log=log)


def data2list(data: dict) -> list:
    return [{"id": i.get("id"), "parent_id": i.get("parent_id"), "mimetype": i.get("mimetype"), "name": i.get("name"),
             "type": i.get("type"), "quote_id": i.get("quote_id"), } for i in data.get("data")]


def make_root(course_id: str) -> TextIO:
    name = (requests.post(url="https://ccnu.ai-augmented.com/api/jx-iresource/statistics/group/visit",
                          data={"group_id": course_id, "role_type": "normal"}, headers=headers, ).json().get(
        "data").get(
        "name"))
    log = open(f"download_filename-{name}.log", "w+", encoding="utf-8")
    log.write("已创建" + os.getcwd() + "\\" + name + "\n")
    log.flush()
    i = 1
    while os.path.exists(name):
        if i == 1:
            log.write(f"{name}-路径已存在")
        try:
            log.write(f"将其重名为{name}({i})")
            os.rename(name, f"{name}({i})")
        except:
            log.write(f"{name}({i})已存在")
            i = i + 1
    os.mkdir(name)
    os.chdir(name)
    return log


def list2tree(file_list: list) -> dict:
    mapping: dict = dict(zip([i["id"] for i in file_list], file_list))
    file_tree: dict = {}
    for i in file_list:
        parent: dict = mapping.get(i["parent_id"])
        if parent is None:
            file_tree: dict = i
        else:
            children: file_list = parent.get("children")
            if not children:
                children: file_list = []
            children.append(i)
            parent.update({"children": children})
    return file_tree


def makedir_and_download(file_tree: dict, headers: dict, video: bool, log) -> None:
    for i in file_tree.get("children"):
        type: str = i.get("type")
        name: str = i.get("name")
        if type == 1:
            os.mkdir(name)
            os.chdir(name)
            log.write("已创建" + os.getcwd() + "\\" + name + "\n")
            log.flush()
            makedir_and_download(file_tree=i, headers=headers, video=video, log=log)
            os.chdir("../")
        elif type == 6:
            download_wps(item_json=i, headers=headers, log=log)
        elif type == 9 and video:
            download_video(item_json=i, headers=headers, log=log)


def download_wps(item_json: dict, headers: dict, log) -> None:
    quote_id: str = item_json.get("quote_id")
    url: str = ("https://ccnu.ai-augmented.com/api/jx-oresource/cloud/file_url/" + quote_id)
    download_url: str = (get_json(url=url, headers=headers).get("data").get("url"))
    with open(item_json.get("name"), "wb+") as f:
        f.write(requests.get(url=download_url).content)
        log.write("已下载" + os.getcwd() + "\\" + item_json.get("name") + "\n")
        log.flush()


def download_video(item_json: dict, headers: dict, log) -> None:
    name: str = item_json.get("name")
    try:
        node_id: str = item_json.get("id")
        get_video_id_url: str = (
                "https://ccnu.ai-augmented.com/api/jx-iresource/resource/queryResource?node_id=" + node_id)
        video_id: str = (get_json(get_video_id_url, headers=headers).get("data").get("resource").get("video_id"))
        get_m3u8_url: str = ("https://ccnu.ai-augmented.com/api/jx-oresource/vod/video/play_auth/" + video_id)
        m3u8_url: str = (
            get_json(url=get_m3u8_url, headers=headers).get("data").get("private_vod")[0].get("private_url"))
        m3u8_list: str = requests.get(url=m3u8_url, headers=headers).text
        ts_list: list = re.findall(pattern=".*?\.ts", string=m3u8_list)
        with open(name, "ab+") as f:
            for i in ts_list:
                url: str = "https://vod-trans-1.ccnu.edu.cn" + i
                f.write(requests.get(url=url, headers=headers).content)
            log.write("已下载" + os.getcwd() + "\\" + name + "\n")
            log.flush()
    except:
        log.write("暂时无法下载" + os.getcwd() + "\\" + name + "\n")
        log.flush()


if __name__ == "__main__":
    Authorization = input("请输入您的Authorization：")
    headers = {"Authorization": Authorization}
    name_list, id_list = get_course(headers=headers)
    choose(name_list=name_list, id_list=id_list)
