import discord
import deepl
from openai import OpenAI
import requests
import re
import os, io, base64
from discord.ext import commands
from discord.commands import slash_command, Option
from dotenv import load_dotenv
from .common.options import model_options, sampler_options, aspect_ratio_options, style_preset_options, clip_guidance_preset_options
from .common.messages import *
import json

load_dotenv()
API_HOST = os.getenv('API_HOST', 'https://api.stability.ai')
API_KEY = os.getenv("STABILITY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")

if not API_KEY:
    raise EnvironmentError("Missing Stability API key.")

class IMAGINE(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(name="art", description=IMAGINE_DESCRIPTION)
    async def imagine(self, ctx,
                      呪文: Option(str, PROMPT_OPTION_DESC, required=True),
                      サイズ: Option(str, ASPECT_OPTION_DESC, choices=list(aspect_ratio_options.keys()), required=False, default="四角"),
                      スタイル: Option(str, STYLE_OPTION_DESC, choices=list(style_preset_options.keys()), required=False, default="写真"),
                      ):
                   
        await ctx.defer()

        # パラメータの変数名を変更
        prompt = 呪文
        aspect = サイズ
        style = スタイル
        orig_prompt = prompt

        # 必要に応じて英語に翻訳
        regex = re.compile(r'[\u30a0-\u30ff\u3040-\u309f\u3005-\u3006\u30e0-\u9fcf]')
        if regex.search(prompt):
            # DEEPL APIを使用してプロンプトを翻訳
            translator = deepl.Translator(DEEPL_API_KEY)
            source_lang = 'JA'
            target_lang = 'EN-US'
            prompt = translator.translate_text(prompt, source_lang=source_lang, target_lang=target_lang).text
        
        # 細かいパラメータはRukiArtが設定してあげる
        model = "Stable Diffusion XL 1.0"
        translated_prompt = "(masterpiece, best quality, extremely detailed), " + prompt
        negative_prompt = "nsfw, (deformed iris, deformed pupils), text, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, (extra fingers), (mutated hands), poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, (fused fingers), (too many fingers), long neck, camera"
        cfg_scale = None
        clip_guidance_preset = "NONE"
        sampler = "K_DPMPP_SDE"
        seed = None

        # リクエスト内容を作成
        width, height = aspect_ratio_options[aspect]
        json_data = {
            "text_prompts": [{"text": translated_prompt, "weight": 1}] + ([{"text": negative_prompt, "weight": -1}] if negative_prompt else []),
            "height": height,
            "width": width,
            "samples": 4,
            "steps": 20,
            **({"cfg_scale": cfg_scale} if cfg_scale else {}),
            **({"clip_guidance_preset": clip_guidance_preset}),
            **({"sampler": sampler} if sampler else {}),
            **({"style_preset": style_preset_options[style]} if style != "None" else {}),
            **({"seed": seed} if seed else {}),
        }

        response = requests.post(f"{API_HOST}/v1/generation/{model_options[model]}/text-to-image", headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }, json=json_data)

        # 失敗したら絵を描くのを中止
        if response.status_code != 200:
            response_dict = json.loads(response.text)
            embed=discord.Embed(
                color=discord.Color.red(), 
                description=
                f"**{ctx.author.mention} ごめんなさい！絵を描くのに失敗しました‥。**\n" +
                f"{response.status_code} {response.reason}：{response_dict['name']}",
            )
            embed.set_footer(text=response_dict['message'])
            await ctx.respond(embed=embed)
            return
        
        # RUKIART専用カスタム
        author_name = ctx.author.display_name
        if author_name == "rukia1243_":
            author_name = "ルキ"

        # GPTによる応答生成
        gpt_system = f"""あなたは「RukiArt」という名前の、25歳日本人女性のイラストレーターです。
あなたは{author_name}という人のお願いを聞いて、絵を描いてあげています。"""
        gpt_user = f"""お願いされて描いた絵を相手の前に置いて見せたときの気分になりきって、#お願い の内容を踏まえて、{author_name}のセンスを褒めたり、満足してもらえたか聞いたり、こだわりポイントを話したり、気の利いたコメントを100文字程度で言ってください。

#お願い
- 依頼内容: {呪文}
- スタイル: {スタイル}

#制約
- 会話の中で、できるだけ自然に{author_name}の名前を呼んであげてください。
- 名前から会話を生成しないでください。具体的には、「{author_name}、」から会話を始めないでください。
- 年上の女性として妹に語り掛けるように話してください。
- 敬語は使わないでください。
- 生成した結果に「」を含めないでください。
"""
        client = OpenAI()
        completion = client.chat.completions.create(
            model="gpt-4-turbo-2024-04-09",
            messages=[
                {"role": "system", "content": gpt_system},
                {"role": "user", "content": gpt_user}
            ]
        )
        # 応答の表示
        gpt_text = completion.choices[0].message.content

        # 投稿の作成
        files = []
        seeds = ""
        nsfw_content_count = 0
        view = discord.ui.View()
        valid_image_index = 0 # 有効な画像のインデックスを追跡するための変数を追加
        for i, image in enumerate(response.json().get("artifacts", [])):

            if "SUCCESS" != image.get("finishReason"):
                nsfw_content_count += 1
                continue

            # ファイルを追加する前に、有効な画像のインデックスを更新
            files.append(discord.File(io.BytesIO(base64.b64decode(image["base64"])), filename=f"image{valid_image_index+1}.png"))
            seeds += f"  - image{valid_image_index+1}: `{image['seed']}`\n"

            # ここでvalid_image_indexを使用してボタンのcustom_idを設定
            button = discord.ui.Button(label=f"{valid_image_index+1}枚目を拡大", custom_id=f"{valid_image_index}")
            view.add_item(button)

            valid_image_index += 1  # ボタンを追加した後でインデックスをインクリメント
            
        if seeds == "":
            embed=discord.Embed(
                color=discord.Color.red(), 
                description=f"{ERROR_CONTENT_DETECTED}",
            )
            embed.set_footer(text=ERROR_CONTENT_DETECTED_DETAIL)
            await ctx.respond(embed=embed)
            return
        
        embed = discord.Embed(
                description=
                    f"**{ctx.author.mention} 絵を描きました！**\n" +
                    f"- 呪文: `{orig_prompt}`\n" +
                    f"- サイズ: `{aspect}({width}:{height})`\n" +
                    (f"- スタイル: `{style}`\n" if style != "None" else "") +
                    (f"\n\n") +
                    (ERROR_NSFW.format(nsfw_content_count) if nsfw_content_count !=0 else ""),
                color=discord.Color.blurple() 
                )
            
        embed.set_thumbnail(url="http://drive.google.com/uc?export=view&id=1eLZoHMl93orIbz-kkaSJYs-d5Y8sYtIh")
        embed.set_footer(text=gpt_text, icon_url=ctx.me.avatar.url)
        await ctx.respond(embed=embed, files=files, view=view)


        async def button_callback(interaction: discord.Interaction):
            await interaction.response.defer()

            original_message = interaction.message
            # button_callback内のcustom_idの取得方法を変更
            custom_id = int(interaction.data["custom_id"])

            # NSFW画像を考慮してインデックスを直接使用
            attachment_url = original_message.attachments[custom_id].url
            response = requests.get(attachment_url)

            if response.status_code != 200:
                embed=discord.Embed(
                    color=discord.Color.red(), 
                    description=ERROR_SYSTEM,
                )
                embed.set_footer(text=ERROR_RETRY)
                await interaction.followup.send(embed=embed)
                return  
            image_data = response.content

            engine_id = "esrgan-v1-x2plus"
            response = requests.post(
                f"{API_HOST}/v1/generation/{engine_id}/image-to-image/upscale",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {API_KEY}"
                },
                files={
                    "image": image_data
                }
            )

            files = []
            for i, image in enumerate(response.json().get("artifacts", [])):
                files.append(discord.File(io.BytesIO(base64.b64decode(image["base64"])), filename=f"image{i+1}.png"))

            embed = discord.Embed(
                description=
                    f"**{ctx.author.mention} 絵を大きくしました！**\n",
                color=discord.Color.blurple() 
            )

            embed.set_thumbnail(url="http://drive.google.com/uc?export=view&id=1eLZoHMl93orIbz-kkaSJYs-d5Y8sYtIh")
            embed.set_footer(text=f"created by {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
            await interaction.followup.send(embed=embed, files=files)

        for item in view.children:
            if isinstance(item, discord.ui.Button):
                item.callback = button_callback

def setup(bot):
    bot.add_cog(IMAGINE(bot))