model_options = {
    "Stable Diffusion XL 1.0": "stable-diffusion-xl-1024-v1-0",
    "Stable Diffusion 1.6": "stable-diffusion-v1-6",
}

sampler_options = {
    "DDIM": 0,
    "DDPM": 1,
    "K_EULER": 2,
    "K_EULER_ANCESTRAL": 3,
    "K_HEUN": 4,
    "K_DPM_2": 5,
    "K_DPM_2_ANCESTRAL": 6,
    "K_LMS": 7,
    "K_DPMPP_2S_ANCESTRAL": 8,
    "K_DPMPP_2M": 9,
    "K_DPMPP_SDE": 10
}

clip_guidance_preset_options = {
    "NONE": 0,
    "FAST_BLUE": 1,
    "FAST_GREEN": 2,
    "SIMPLE": 3,
    "SLOW": 4,
    "SLOWER": 5,
    "SLOWEST": 6,
}

aspect_ratio_options = {
    "四角": (1024, 1024),
    "小横長": (1152, 896),
    "中横長": (1216, 832),
    "大横長": (1344, 768),
    "超横長": (1536, 640),
    "小縦長": (896, 1152),
    "中縦長": (832, 1216),
    "大縦長": (768, 1344),
    "超縦長": (640, 1536),
}

style_preset_options = {
    '指定なし': 'none',
    '3Dモデル': '3d-model', 
    '写真': 'photographic',
    'アニメ': 'anime',
    '映画風': 'cinematic',
    'アナログフィルム': 'analog-film',
    'ファンタジー': 'fantasy-art',
    '線画': 'line-art',
    'ドット絵': 'pixel-art',
    'アメリカンコミック': 'comic-book',
    'デジタルアート': 'digital-art',
    'ネオンパンク': 'neon-punk',
    '折り紙': 'origami',
    'ローポリ': 'low-poly',
    '粘土風': 'modeling-compound',
    '強化補正': 'enhance',
    '等角投影': 'isometric',
    'タイルテクスチャ': 'tile-texture'
}