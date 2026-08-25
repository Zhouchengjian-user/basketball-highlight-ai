import re

import pytest

from commentary_style import (
    LIVE_SPOKEN_PATTERNS,
    MAX_SCENE_HINTS_PER_EVENT,
    MAX_SCENE_HINTS_TOTAL,
    ORIGINAL_BROADCAST_LEXICON,
    ORIGINAL_SCENE_PHRASES,
    critical_rhythm_issues,
    lint_beats,
    load_delivery_profile,
    load_style,
    minimum_natural_chars,
)


ROBOTIC_FIVE_CHAR_BEATS = [
    "快速推进传，找位空切跑。",
    "突破起跳投，篮球刷网进。",
    "白队发底线，外线接球稳。",
    "拔起投篮偏，篮板被抢下。",
    "红队断球下，加速杀禁区。",
    "面对补防扰，高难抛投出。",
]

NATURAL_LIVE_BEATS = [
    "比赛一上来就提速，白队从右侧把球带过半场。",
    "一个交叉步甩开防守，直冲篮下！",
    "协防收得很快，这次出手没能落袋。",
    "黑队保护住篮板，马上推转换。",
    "速度没完全起来，那就先稳一稳。",
    "高位掩护已经到位，持球人往中路走。",
    "两个人被带走，底角空间出来了。",
    "分到底角！",
    "出手，有了！",
    "这一攻打得很耐心，先收进防守，再找到空位。",
]


def test_five_character_march_is_rejected():
    codes = {issue.code for issue in lint_beats(ROBOTIC_FIVE_CHAR_BEATS)}
    assert "FIVE_CHAR_MARCH" in codes
    assert "MONOTONOUS_LENGTH" in codes
    assert "MISSING_FULL_SENTENCE" in codes
    assert "FRAGMENT" in codes


def test_three_consecutive_five_character_units_are_rejected():
    issues = lint_beats(["白队在推进。", "防守正收缩。", "黑队推反击。"])
    assert "FIVE_CHAR_MARCH" in {issue.code for issue in issues}


def test_one_short_burst_is_allowed_inside_natural_commentary():
    assert critical_rhythm_issues(NATURAL_LIVE_BEATS) == []


def test_a_single_natural_five_character_line_is_not_banned():
    issues = lint_beats(["先稳住节奏。", "防守已经收到了篮下。", "分到底角！"])
    assert "FIVE_CHAR_MARCH" not in {issue.code for issue in issues}


def test_comma_packing_cannot_hide_five_character_march():
    issues = lint_beats(["快速推进传，找位空切跑，突破起跳投，篮球刷网进。"])
    assert "FIVE_CHAR_MARCH" in {issue.code for issue in issues}


def test_four_to_seven_character_cadence_grid_is_rejected():
    issues = lint_beats(
        ["快速推进，外线接球以后，立刻转身，防守重新落位。"]
    )
    assert "SHORT_CADENCE_GRID" in {issue.code for issue in issues}


def test_style_registry_is_fixed_and_exposes_three_stage_rules():
    skill = load_style("basketball_live")
    planner = skill.planner_rules(30.0, 9, 115, 128, 138)
    rewrite = skill.rewrite_rules(lint_beats(ROBOTIC_FIVE_CHAR_BEATS), 9, 115, 128, 138)
    assert skill.label == "活人感篮球解说 Skill"
    assert "只提供事实材料" in skill.observation_rules()
    assert "禁止把每段都写成“五字，五字”" in planner
    assert "夸赞与氛围" in planner
    assert "好球" in planner
    assert "漂亮" in planner
    assert "每三个 beat 最多有一处显性夸赞" in planner
    assert "现场口语动作" in planner
    assert "有了！" in planner
    assert "断下来了！" in planner
    assert "感谢收看" in planner
    assert "FIVE_CHAR_MARCH" in rewrite
    assert "一口气自然衔接" in skill.tts_group_rules(True, True, True)
    with pytest.raises(ValueError, match="未知解说风格包"):
        load_style("user-supplied-module")


def test_natural_minimum_budget_does_not_force_tiny_segments():
    assert minimum_natural_chars(2) == 17
    assert minimum_natural_chars(3) == 24
    assert minimum_natural_chars(15) >= 105


def test_original_broadcast_profile_has_a_large_original_safe_lexicon():
    expressions = [
        text
        for category in ORIGINAL_BROADCAST_LEXICON.values()
        for text in category
    ]
    assert len(ORIGINAL_BROADCAST_LEXICON) >= 12
    assert len(expressions) >= 100
    assert len(expressions) == len(set(expressions))
    joined = "".join(expressions)
    assert "于嘉" not in joined
    assert "央视" not in joined


def test_live_spoken_pattern_bank_is_large_original_and_event_bound():
    expressions = [
        text
        for patterns in LIVE_SPOKEN_PATTERNS.values()
        for text in patterns
    ]
    assert len(LIVE_SPOKEN_PATTERNS) >= 10
    assert len(expressions) >= 50
    assert len(expressions) == len(set(expressions))
    joined = "".join(expressions)
    assert "于嘉" not in joined
    assert "央视" not in joined
    assert "腾讯" not in joined
    assert not re.search(r"兄弟们|家人们|感谢收看|下次再见", joined)
    for term in ("再转一手", "起速了", "抬手就投", "有了", "断下来了", "走，反击"):
        assert term in joined


def test_original_broadcast_profile_prioritizes_live_evidence_and_no_imitation():
    profile = load_delivery_profile("broadcast_original")
    planner = profile.planner_rules(30.0)
    assert profile.label == "原创专业篮球转播叙事"
    assert "现场节奏永远先于背景信息" in planner
    assert "后续新动作一出现，尚未播出的解释立即让位给现场" in planner
    assert "不得新增比分、人物经历、数据、队名、命中结果或判罚" in planner
    assert "真实解说员姓名" in planner
    instruction = profile.compact_tts_instruction("hype")
    assert "专业篮球现场转播" in instruction
    assert "不模仿真人" in instruction
    with pytest.raises(ValueError, match="未知解说表达配置"):
        load_delivery_profile("public-figure-imitation")


def test_structured_scene_phrases_have_evidence_and_result_boundaries():
    assert len(ORIGINAL_SCENE_PHRASES) >= 24
    assert len({phrase.id for phrase in ORIGINAL_SCENE_PHRASES}) == len(
        ORIGINAL_SCENE_PHRASES
    )
    all_templates = [
        template
        for phrase in ORIGINAL_SCENE_PHRASES
        for template in phrase.templates
    ]
    assert len(all_templates) == len(set(all_templates))
    assert all(phrase.event_kinds for phrase in ORIGINAL_SCENE_PHRASES)
    assert all(phrase.templates for phrase in ORIGINAL_SCENE_PHRASES)

    result_claim = re.compile(
        r"命中|打进|得分|进了|没进|未进|打铁|弹框|弹筐|偏出"
    )
    for phrase in ORIGINAL_SCENE_PHRASES:
        if phrase.event_kinds == frozenset({"shot"}):
            assert not any(result_claim.search(text) for text in phrase.templates)
        if phrase.event_kinds == frozenset({"made_shot"}):
            assert all(
                re.match(r"^(?:命中|打进|有了|进了)！", text)
                for text in phrase.templates
            )
        if phrase.event_kinds == frozenset({"missed_shot"}):
            assert all(re.match(r"^(?:没进|未进)！", text) for text in phrase.templates)
        if phrase.event_kinds == frozenset({"stoppage"}):
            assert not any(
                re.search(r"犯规|罚球|打手|阻挡|暂停回来|重新发球", text)
                for text in phrase.templates
            )
        if phrase.event_kinds == frozenset({"block"}):
            assert not any(
                re.search(r"出手|投篮|上篮|抛投|扣篮", text)
                for text in phrase.templates
            )
        if phrase.phase == "result":
            assert not any(
                re.search(r"结果已经确认|结果落定|局面变化|改变.{0,4}比分", text)
                for text in phrase.templates
            )


def test_professional_scene_vocabulary_covers_full_basketball_flow():
    joined = "".join(
        template
        for phrase in ORIGINAL_SCENE_PHRASES
        for template in phrase.templates
    )
    for term in (
        "击地传球",
        "大范围转移",
        "口袋传球",
        "突分",
        "手递手",
        "传切",
        "空切",
        "面框单打",
        "低位背身",
        "胯下运球",
        "背后运球",
        "欧洲步",
        "杀入篮下",
        "三分出手",
        "急停跳投",
        "后撤步",
        "抛投",
        "勾手",
        "反篮",
        "空中接力",
        "上篮得手",
        "火锅",
        "卡位",
        "快攻",
        "一条龙",
        "挡拆",
        "顺下",
        "外弹",
        "夹击",
        "换防",
        "轮转",
        "护框",
    ):
        assert term in joined
    assert "造犯规" not in joined


def test_planner_rules_no_longer_inject_the_full_legacy_lexicon():
    profile = load_delivery_profile("broadcast_original")
    planner = profile.planner_rules(30.0)
    assert "具体表达候选会在音画事件确认后" in planner
    assert ORIGINAL_BROADCAST_LEXICON["球权与起势"][0] not in planner
    assert ORIGINAL_BROADCAST_LEXICON["回合收束"][-1] not in planner


def test_scene_hints_are_filtered_by_kind_evidence_and_confidence():
    profile = load_delivery_profile("broadcast_original")
    hints = profile.scene_hints(
        [
            {
                "event_id": "shot-1",
                "kind": "shot",
                "action": "弧顶起跳出手，防守及时扑防",
                "result": "无法确认",
                "confidence": 0.91,
            },
            {
                "event_id": "pass-1",
                "kind": "pass",
                "action": "球传到底角弱侧",
                "result": "",
                "confidence": 0.88,
            },
            {
                "event_id": "screen-low",
                "kind": "other",
                "action": "高位掩护",
                "result": "",
                "confidence": 0.51,
            },
        ]
    )
    shot_line = next(line for line in hints.splitlines() if "shot-1" in line)
    pass_line = next(line for line in hints.splitlines() if "pass-1" in line)
    assert not re.search(r"命中|打进|没进|未进|得分", shot_line)
    assert any(word in pass_line for word in ("底角", "弱侧", "外侧", "另一边"))
    assert "screen-low" not in hints


def test_confirmed_made_shot_gets_one_fact_and_one_praise_candidate():
    profile = load_delivery_profile("broadcast_original")
    hints = profile.scene_hints(
        [
            {
                "event_id": "made-praise-1",
                "kind": "made_shot",
                "action": "篮球清楚落入篮筐",
                "result": "命中",
                "confidence": 0.95,
            }
        ]
    )
    line = next(line for line in hints.splitlines() if "made-praise-1" in line)

    assert "／" in line
    assert any(word in line for word in ("落入篮筐", "落进篮筐", "命中", "打进"))
    assert any(word in line for word in ("好球", "漂亮", "处理得真好", "干净利落"))


def test_praise_budget_reserves_a_slot_for_a_later_confirmed_result():
    profile = load_delivery_profile("broadcast_original")
    events = [
        {
            "event_id": "pass-praise-1",
            "kind": "pass",
            "action": "一记击地传球穿过防守",
            "result": "",
            "confidence": 0.94,
            "detail_tags": ["bounce_pass"],
        },
        {
            "event_id": "drive-praise-1",
            "kind": "drive",
            "action": "交叉变向以后继续突破",
            "result": "",
            "confidence": 0.93,
            "detail_tags": ["crossover"],
        },
        {
            "event_id": "shot-praise-1",
            "kind": "shot",
            "action": "接球即投，篮球已经离手",
            "result": "无法确认",
            "confidence": 0.92,
            "detail_tags": ["catch_and_shoot"],
        },
        {
            "event_id": "pass-praise-2",
            "kind": "pass",
            "action": "一记口袋传球送进防守缝隙",
            "result": "",
            "confidence": 0.91,
            "detail_tags": ["pocket_pass"],
        },
        {
            "event_id": "made-praise-late",
            "kind": "made_shot",
            "action": "篮球落入篮筐",
            "result": "命中",
            "confidence": 0.95,
        },
    ]

    hints = profile.scene_hints(events)
    praise_terms = re.compile(r"好球|漂亮|好传|真及时|真好|真稳|扎实|果断|坚决")
    praised_lines = [
        line
        for line in hints.splitlines()
        if line.startswith("- ") and praise_terms.search(line)
    ]
    result_line = next(line for line in hints.splitlines() if "made-praise-late" in line)

    assert len(praised_lines) <= 2
    assert praise_terms.search(result_line)


def test_strong_contact_praise_requires_same_chain_local_verification():
    profile = load_delivery_profile("broadcast_original")
    base = {
        "kind": "made_shot",
        "action": "强对抗中出手，篮球随后落入篮筐",
        "result": "命中",
        "confidence": 0.96,
        "detail_tags": ["through_contact"],
    }
    unverified = profile.scene_hints(
        [{**base, "event_id": "contact-unverified"}]
    )
    verified = profile.scene_hints(
        [
            {
                **base,
                "event_id": "contact-verified",
                "verified_detail_tags": ["through_contact"],
                "chain_id": "contact-chain-1",
            }
        ]
    )

    assert not re.search(r"够硬|顶着对抗|身体接触以后|强对抗下", unverified)
    assert re.search(r"够硬|顶着对抗|身体接触以后|强对抗下", verified)


def test_plain_contest_never_unlocks_body_contact_praise():
    profile = load_delivery_profile("broadcast_original")
    hints = profile.scene_hints(
        [
            {
                "event_id": "contest-only",
                "kind": "made_shot",
                "action": "防守扑到面前形成干扰，篮球随后落入篮筐",
                "result": "命中",
                "confidence": 0.95,
                "detail_tags": ["contested_shot"],
                "verified_detail_tags": ["contested_shot"],
                "chain_id": "contest-chain-1",
            }
        ]
    )

    assert "面对干扰" in hints or "干扰已经" in hints or "防守贴到" in hints
    assert not re.search(r"够硬|顶着对抗|身体接触以后|强对抗下", hints)


def test_made_shot_technique_hint_requires_same_chain_verified_tag():
    profile = load_delivery_profile("broadcast_original")
    base = {
        "kind": "made_shot",
        "action": "篮球落入篮筐",
        "result": "命中",
        "confidence": 0.96,
        "detail_tags": ["layup"],
    }
    unverified = profile.scene_hints(
        [{**base, "event_id": "made-unverified"}]
    )
    verified = profile.scene_hints(
        [
            {
                **base,
                "event_id": "made-verified",
                "verified_detail_tags": ["layup"],
                "chain_id": "shot-chain-1",
            }
        ]
    )

    assert "上篮" not in unverified
    assert "上篮" in verified


def test_generic_outer_shot_hint_never_unlocks_three_pointer():
    profile = load_delivery_profile("broadcast_original")
    hints = profile.scene_hints(
        [
            {
                "event_id": "outer-shot",
                "kind": "shot",
                "action": "外线起跳出手",
                "result": "无法确认",
                "confidence": 0.95,
                "detail_tags": [],
            }
        ]
    )

    assert "三分" not in hints


def test_three_point_scene_wording_requires_local_verified_tag():
    profile = load_delivery_profile("broadcast_original")
    event = {
        "kind": "shot",
        "action": "双脚在三分线外，篮球已经离手",
        "result": "无法确认",
        "confidence": 0.95,
        "detail_tags": ["three_point"],
    }
    coarse = profile.scene_hints([{**event, "event_id": "coarse-three"}])
    reviewed = profile.scene_hints(
        [
            {
                **event,
                "event_id": "reviewed-three",
                "verified_detail_tags": ["three_point"],
                "chain_id": "three-chain",
            }
        ]
    )

    assert "三分" not in coarse
    assert "三分" in reviewed


def test_scene_hints_do_not_swap_neighboring_tactical_terms():
    profile = load_delivery_profile("broadcast_original")
    hints = profile.scene_hints(
        [
            {
                "event_id": "help-1",
                "kind": "pass",
                "action": "协防向持球一侧移动，球随后传出",
                "result": "",
                "confidence": 0.94,
            },
            {
                "event_id": "switch-1",
                "kind": "drive",
                "action": "掩护后防守明确换防",
                "result": "",
                "confidence": 0.94,
            },
        ]
    )
    help_line = next(line for line in hints.splitlines() if "help-1" in line)
    switch_line = next(line for line in hints.splitlines() if "switch-1" in line)
    assert "协防" in help_line
    assert "换防" not in help_line
    assert "轮转" not in help_line
    assert "换防" in switch_line
    assert "协防" not in switch_line
    assert "轮转" not in switch_line


def test_generic_shot_hint_does_not_invent_defensive_pressure():
    profile = load_delivery_profile("broadcast_original")
    hints = profile.scene_hints(
        [
            {
                "event_id": "open-shot",
                "kind": "shot",
                "action": "弧顶起跳出手",
                "result": "无法确认",
                "confidence": 0.93,
            }
        ]
    )
    shot_line = next(line for line in hints.splitlines() if "open-shot" in line)
    assert not re.search(r"防守|干扰|扑防|贴防|封堵", shot_line)


def test_critical_scene_hints_require_explicit_critical_time_context():
    profile = load_delivery_profile("broadcast_original")
    event = {
        "event_id": "pos-1",
        "kind": "possession",
        "action": "持球人在前场组织",
        "result": "",
        "confidence": 0.91,
    }
    ordinary = profile.scene_hints([event])
    with_score = profile.scene_hints(
        [event],
        game_context={"score_text": "飞跃队 12:10 南城队"},
    )
    with_clock = profile.scene_hints(
        [event],
        trusted_context="末节还剩18秒",
    )
    with_period_only = profile.scene_hints(
        [event],
        trusted_context="比赛进入末节",
    )
    assert "时间压力已经到了" not in ordinary
    assert "关键阶段" not in ordinary
    assert not any(
        word in with_score for word in ("时间压力", "关键阶段", "比赛来到")
    )
    assert any(word in with_clock for word in ("时间压力", "关键阶段", "比赛来到"))
    assert "时间压力" not in with_period_only
    assert "关键阶段" not in with_period_only


def test_scene_hint_selector_enforces_per_event_and_total_limits():
    profile = load_delivery_profile("broadcast_original")
    events = [
        {
            "event_id": f"pass-{index}",
            "kind": "pass",
            "action": "协防轮转以后把球传到底角弱侧",
            "result": "",
            "confidence": 0.95,
        }
        for index in range(30)
    ]
    hints = profile.scene_hints(events)
    lines = [line for line in hints.splitlines() if line.startswith("- ")]
    selected_count = sum(line.count("／") + 1 for line in lines)
    assert selected_count <= MAX_SCENE_HINTS_TOTAL
    assert all(line.count("／") + 1 <= MAX_SCENE_HINTS_PER_EVENT for line in lines)
