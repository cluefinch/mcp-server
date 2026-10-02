from mcp_search.excerpt import _tokenize, select_excerpts


def test_cjk_tokenizer_uses_overlapping_bigrams():
    assert _tokenize("人工智能") == ["人工", "工智", "智能"]
    assert _tokenize("AI 人工智能") == ["ai", "人工", "工智", "智能"]
    assert _tokenize("猫") == ["猫"]


def test_chinese_query_ranks_matching_later_passage():
    leading = "这是一个关于天气预报和城市交通的普通段落。" * 4
    matching = "这项研究讨论人工智能模型训练、推理效率以及机器学习系统的发展。" * 4
    text = leading + "\n\n" + matching

    excerpts = select_excerpts(text, ["人工智能"])

    assert excerpts
    assert "人工智能" in excerpts[0]["text"]
    assert excerpts[0]["start_char"] > 0
    assert (
        excerpts[0]["text"] == text[excerpts[0]["start_char"] : excerpts[0]["end_char"]]
    )


def test_japanese_query_ranks_matching_later_passage():
    leading = "この段落では天気予報と都市交通について説明しています。" * 4
    matching = (
        "この研究では人工知能モデルの学習と推論性能について詳しく分析します。" * 4
    )
    text = leading + "\n\n" + matching

    excerpts = select_excerpts(text, ["人工知能"])

    assert excerpts
    assert "人工知能" in excerpts[0]["text"]
    assert (
        excerpts[0]["text"] == text[excerpts[0]["start_char"] : excerpts[0]["end_char"]]
    )
