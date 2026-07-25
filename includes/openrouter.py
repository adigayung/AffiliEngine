# File Name : libs/openrouter.py
# Description : Configuration module for image captioning using custom prompts with locally downloaded LLMs or hosted LLMs via OpenRouter
# Provides global settings such as API port, UI theme (dark mode), available model list, and hardware preferences (GPU/CPU)
# This file centralizes environment settings to support flexible deployment and easy model switching
# Specifically designed for single-image captioning tasks using vision-capable LLMs
# Author : Adi Gayung Mantik, S.Kom
# Repository : https://github.com/adigayung/LLM-vision-Captioning
# License : MIT

from openai import OpenAI
import base64
import os
import re
from includes.logFX import logger

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
def LLM_OpenRouter(model, apikey, prompt, imgPath=None, single=True, api_url="https://openrouter.ai/api/v1", site_url="https://github.com/adigayung/LLM-vision-Captioning", site_title="LLM-vision-Captioning"):
    logger("info", f"Menggunakan Model : {model}")
    client = OpenAI(
        base_url=api_url,
        api_key=apikey,
    )

    extra_headers = {}
    if site_url:
        extra_headers["HTTP-Referer"] = site_url
    if site_title:
        extra_headers["X-Title"] = site_title
    if imgPath :
        base64_image = encode_image_to_base64(imgPath)
        ImgURL = f"data:image/jpeg;base64,{base64_image}"


    try:
        if imgPath :
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": ImgURL}}
                        ]
                    }
                ],
                extra_headers=extra_headers,
                extra_body={}
            )
        else:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                extra_headers=extra_headers,
                extra_body={}
            )
        hasilnya = response.choices[0].message.content

        if single==False:
            txt_path = os.path.splitext(imgPath)[0] + ".txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(hasilnya)
        return hasilnya
    except Exception as e:
        return f"[ERROR] {e}"

def clean_llm_output(text: str) -> str:
    """
    Bersihkan output LLM dengan memotong bagian pembuka jika ada ':' di baris pertama.
    Return hanya deskripsi (biasanya baris kedua dan seterusnya).
    """
    lines = text.strip().splitlines()

    # Jika ada ":" di baris pertama, buang baris itu
    if lines and ":" in lines[0]:
        lines = lines[1:]

    # Gabung kembali isi setelah baris pertama
    result = "\n".join(lines).strip()

    # Hapus titik di akhir jika ada
    if result.endswith('.'):
        result = result[:-1]

    return result