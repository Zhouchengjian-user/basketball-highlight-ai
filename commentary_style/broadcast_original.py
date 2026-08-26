from __future__ import annotations

import re
from collections.abc import Mapping as MappingABC, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


# These are project-original semantic scaffolds, not quotations or catchphrases from
# any real commentator. The language model may use them only when video evidence fits.
ORIGINAL_BROADCAST_LEXICON: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "球权与起势": (
            "先把球稳稳带到前场",
            "这一回合从弧顶开始组织",
            "持球人先观察防守站位",
            "进攻方没有急着处理",
            "球权控制下来以后再找机会",
            "防守已经贴到持球人身前",
            "这一攻先从强侧发起",
            "场上节奏暂时压了下来",
            "持球人把队友的位置看了一遍",
            "进攻落到半场阵地",
        ),
        "空间与站位": (
            "两侧把空间充分拉开",
            "弱侧底角暂时留出了位置",
            "内线一收，外线空间就出现了",
            "强侧人多，球需要尽快转出去",
            "防守重心已经偏向持球一侧",
            "篮下空间被防守压得很小",
            "底线有人牵住了协防",
            "弧顶和底角之间形成了传球角度",
            "弱侧没有站死，还在继续移动",
            "这次落位把球场宽度用出来了",
        ),
        "掩护与挡拆": (
            "高位掩护已经提了上来",
            "持球人借掩护往中路走",
            "防守选择换人跟防",
            "两个人夹住了持球线路",
            "顺下队员已经切向篮下",
            "掩护以后没有停，继续往里压",
            "持球人绕出半步出手空间",
            "防守绕过掩护重新追了回来",
            "挡拆把内线防守带到了外面",
            "掩护质量不错，进攻机会随之打开",
        ),
        "传球与阅读": (
            "第一选择没有出现，那就再传一次",
            "球及时送到了弱侧",
            "协防刚一移动，传球就跟了过去",
            "这次分球比防守轮转更快",
            "球从人群里准确找到了外线",
            "没有勉强出手，而是继续寻找空位",
            "传球把两名防守人同时带走",
            "接球以后没有停顿，马上处理",
            "强弱侧完成了一次快速转移",
            "多传一步，机会变得更完整",
        ),
        "突破与终结": (
            "第一步已经抢到了身位",
            "持球人变向以后直奔篮下",
            "防守被迫从侧后方追赶",
            "协防来到篮下，终结难度上来了",
            "最后一步把身体控制得很好",
            "迎着补防把球送向篮板",
            "突破吸引了两个人收缩",
            "从防守缝隙里找到了一条线路",
            "这次攻筐没有躲开身体对抗",
            "篮下处理得很耐心，等防守先落地",
        ),
        "投篮与结果": (
            "空位已经出来，可以起手",
            "接球调整一下，抬手出球",
            "防守扑得很凶，出手仍然完成",
            "球已经离手，先看落点",
            "这一球稳稳落进篮筐",
            "出手没有命中，篮板还在争夺",
            "第一下没进，二次机会还在",
            "出手弧线很完整，结果也有了",
            "这次机会创造得很好，只差最后一下",
            "防守给出的空间被及时利用",
        ),
        "攻守转换": (
            "球权一换，推进速度马上起来",
            "防守还没落位，反击已经到了前场",
            "前场人数占优，需要尽快处理",
            "抢下球以后没有任何停顿",
            "退防先保护篮下，再去找外线人",
            "转换机会没打成，重新落回阵地",
            "第一传把反击速度带了起来",
            "持球人一路把防线压向篮下",
            "追防正在回位，窗口不会停留太久",
            "从防守成功直接接上了下一次进攻",
        ),
        "防守与对位": (
            "上线防守先把中路堵住",
            "领防人没有轻易失去位置",
            "弱侧协防已经提前收进来",
            "换防以后对位没有乱",
            "防守把持球人赶向了边线",
            "篮下有人护住最后一道位置",
            "这次轮转把空位及时补上",
            "对球压力让进攻只能重新组织",
            "防守没有贸然下手，先守住路线",
            "最后一下干扰把出手难度推高了",
        ),
        "篮板与二次进攻": (
            "球弹出来，篮板位置要先卡住",
            "第一点没有拿稳，双方还在争",
            "防守方把篮板牢牢保护下来",
            "进攻篮板留下了第二次机会",
            "篮板控制以后先抬头看前场",
            "内线连续起跳把球点了出来",
            "外围队员收下长篮板",
            "这一回合还没结束，球仍在进攻方手里",
        ),
        "关键时刻": (
            "时间继续往下走，每次处理都更重要",
            "这一攻需要耐心，也需要果断",
            "球到了最适合处理的人手里",
            "防守没有退路，进攻也不能犹豫",
            "先把战术跑完整，再决定最后选择",
            "机会只出现一瞬间，出手必须坚决",
            "这一回合正在改变场上的节奏",
            "关键阶段，比拼的是每一个细节",
            "结果已经确认，情绪在这一刻释放",
            "高压之下，动作依然完成得很清楚",
        ),
        "停顿与调整": (
            "这次对抗以后，回合暂时停了下来",
            "比赛进入短暂停顿，双方重新落位",
            "节奏慢下来，场上需要重新梳理",
            "暂停回来以后，先看防守如何调整",
            "两边借这个间隙重新确认对位",
            "回合停住了，刚才的空间选择值得再看",
        ),
        "回合收束": (
            "这一攻先改变防守，再找到最后机会",
            "从落位到出手，整个回合衔接得很完整",
            "得分只是结果，前面的耐心同样关键",
            "防守完成任务，反击自然随之而来",
            "这一回合的转折来自那次及时协防",
            "空间被一点点打开，机会最终出现",
            "关键动作很短，前面的准备并不短",
            "比赛的节奏，就在这一攻里发生变化",
            "结果落定以后，双方马上要面对下一回合",
            "把复杂的防守读懂，进攻就会变得简单",
        ),
    }
)


MAX_SCENE_HINTS_PER_EVENT = 2
MAX_SCENE_HINTS_TOTAL = 18


@dataclass(frozen=True)
class OriginalScenePhrase:
    """One original expression family unlocked only by matching event evidence.

    The templates are writing directions for the planner, never quotations from
    a real broadcast.  ``required_any`` and ``required_all`` deliberately match
    only the event ledger's action/result text; a scene cannot be unlocked by a
    voice profile name or by a model's desire to make the call more dramatic.
    """

    id: str
    category: str
    event_kinds: frozenset[str]
    phase: str
    templates: tuple[str, ...]
    required_any: tuple[str, ...] = ()
    required_all: tuple[str, ...] = ()
    required_tags: tuple[str, ...] = ()
    requires_verified_tag: bool = False
    is_praise: bool = False
    min_confidence: float = 0.72
    requires_critical_context: bool = False


# This is the evidence-gated production lexicon.  The older mapping above stays
# exported for callers that display the original category catalogue, but it is
# no longer injected wholesale into a planner prompt.
ORIGINAL_SCENE_PHRASES: tuple[OriginalScenePhrase, ...] = (
    OriginalScenePhrase(
        id="possession_generic",
        category="球权与起势",
        event_kinds=frozenset({"possession"}),
        phase="action",
        templates=(
            "球到手，先稳一下，这一攻不着急。",
            "先把球拿住，进攻接着往下走。",
            "球还在进攻方手里，回合继续。",
            "这一回合先稳下来，再往下组织。",
            "先不急，持球人把节奏压下来。",
            "球权拿稳了，接着寻找下一步。",
        ),
    ),
    OriginalScenePhrase(
        id="possession_frontcourt",
        category="球权与起势",
        event_kinds=frozenset({"possession"}),
        phase="action",
        templates=(
            "球来到进攻端，这一回合开始组织。",
            "持球人稳住前场球权，接着寻找机会。",
            "球已经推进到进攻端，队友开始落位。",
            "进攻端的球权稳住，回合继续展开。",
        ),
        required_any=("前场", "弧顶", "外线组织"),
    ),
    OriginalScenePhrase(
        id="possession_pressure",
        category="防守与对位",
        event_kinds=frozenset({"possession"}),
        phase="reaction",
        templates=(
            "防守已经贴上来，持球空间正在变小。",
            "防守人给足压力，这一攻需要耐心处理。",
            "持球人面前有压力，先把球保护下来。",
        ),
        required_any=("贴防", "领防", "防守压力", "紧逼"),
    ),
    OriginalScenePhrase(
        id="pass_generic",
        category="传球与阅读",
        event_kinds=frozenset({"pass"}),
        phase="action",
        templates=(
            "球给出来了，进攻还在往下走。",
            "分球送出，接球队员马上接上。",
            "这一传没有停顿，球继续流动。",
            "往外给，回合还在继续。",
            "球从手里送出，传到下一点。",
            "传球给出去，这一攻接着打。",
        ),
    ),
    OriginalScenePhrase(
        id="pass_weakside",
        category="空间与站位",
        event_kinds=frozenset({"pass"}),
        phase="reaction",
        templates=(
            "球转向外侧，进攻宽度随之打开。",
            "这一传送到另一边，球场被重新拉开。",
            "球及时转向另一侧，进攻继续展开。",
            "传球找到外侧位置，防守需要继续移动。",
        ),
        required_any=("弱侧", "外侧", "底角", "另一侧"),
    ),
    OriginalScenePhrase(
        id="pass_rotation",
        category="传球与阅读",
        event_kinds=frozenset({"pass"}),
        phase="reaction",
        templates=(
            "防守出现移动，球也跟着转了出去。",
            "防守重心一动，这一传马上送向别处。",
            "防守位置发生变化，传球及时完成转移。",
        ),
        required_any=("协防", "轮转", "包夹"),
    ),
    OriginalScenePhrase(
        id="pass_bounce",
        category="传球与阅读",
        event_kinds=frozenset({"pass"}),
        phase="action",
        templates=(
            "一记击地传球，球从防守身边穿了过去。",
            "球走地面，这记击地传球送得很及时。",
            "击地传球送出，接球队员顺势拿到球。",
        ),
        required_any=("击地传球", "反弹传球"),
        min_confidence=0.76,
    ),
    OriginalScenePhrase(
        id="pass_skip",
        category="传球与阅读",
        event_kinds=frozenset({"pass"}),
        phase="reaction",
        templates=(
            "大范围转移找到另一侧，防守要继续移动。",
            "球直接越过中间防守，送到了球场另一边。",
            "一记跨场转移，强弱侧马上发生变化。",
        ),
        required_any=("大范围转移", "跨场传球", "越过防守", "长距离横传"),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="pass_pocket",
        category="传球与阅读",
        event_kinds=frozenset({"pass"}),
        phase="action",
        templates=(
            "球从两名防守之间塞进去，这记口袋传球很及时。",
            "一记口袋传球送到顺下线路，窗口抓得很准。",
            "防守缝隙刚出现，球已经从口袋位置送了进去。",
        ),
        required_any=("口袋传球", "防守缝隙传球"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="pass_drive_kick",
        category="传球与阅读",
        event_kinds=frozenset({"pass"}),
        phase="reaction",
        templates=(
            "突破吸引防守以后及时突分，外侧机会出来了。",
            "人往里走，球再分向外侧，这次突分很清楚。",
            "防守收进篮下，持球人马上把球分了出来。",
        ),
        required_any=("突分", "突破分球", "突破后分球"),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="pass_handoff",
        category="传球与阅读",
        event_kinds=frozenset({"pass", "possession"}),
        phase="action",
        templates=(
            "两个人完成手递手，持球方向随之改变。",
            "手递手接上，进攻继续向另一侧展开。",
            "球在身边完成交接，这次手递手衔接得很顺。",
        ),
        required_any=("手递手", "手递手传球"),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="pass_give_and_go",
        category="传球与阅读",
        event_kinds=frozenset({"pass", "drive", "other"}),
        phase="reaction",
        templates=(
            "球给出去以后立即切入，这次传切开始形成。",
            "传球之后没有停，无球切入马上接了上来。",
            "给球、切入，这次传切衔接得很清楚。",
        ),
        required_any=("传切", "传球后空切", "给出球后切入"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="off_ball_cut",
        category="无球移动",
        event_kinds=frozenset({"pass", "drive", "other"}),
        phase="action",
        templates=(
            "无球人突然空切，直接跑向篮下空间。",
            "一个背切绕到防守身后，接球线路出来了。",
            "反跑切入已经启动，无球一侧正在找空当。",
        ),
        required_any=("空切", "背切", "反跑切入", "无球切入"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="pass_skill_praise",
        category="现场夸赞",
        event_kinds=frozenset({"pass"}),
        phase="reaction",
        templates=(
            "这球传得漂亮，进攻一下流动起来。",
            "好传！这一下把球及时送了出去。",
            "传得真及时，进攻马上接着往下打。",
            "这一传处理得真好，进攻继续往下打。",
        ),
        required_tags=(
            "bounce_pass",
            "skip_pass",
            "pocket_pass",
            "drive_and_kick",
            "handoff",
            "give_and_go",
            "lob_pass",
        ),
        is_praise=True,
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="drive_generic",
        category="突破与终结",
        event_kinds=frozenset({"drive"}),
        phase="action",
        templates=(
            "起速了，持球人开始往里走。",
            "这一步压进去，突破节奏起来了。",
            "人往篮下去了，回合开始提速。",
            "脚步启动，持球人继续往里压。",
            "突破没停，还在向篮筐靠近。",
            "空间一出来，持球人马上启动。",
        ),
    ),
    OriginalScenePhrase(
        id="drive_change_direction",
        category="突破与终结",
        event_kinds=frozenset({"drive"}),
        phase="action",
        templates=(
            "方向一变，持球人继续向里走。",
            "方向突然一变，防守脚步需要重新调整。",
            "持球方向已经改变，突破还在继续。",
        ),
        required_any=("变向", "交叉步", "转身"),
    ),
    OriginalScenePhrase(
        id="drive_paint",
        category="突破与终结",
        event_kinds=frozenset({"drive"}),
        phase="reaction",
        templates=(
            "持球人已经杀入篮下，终结距离更近了。",
            "人已经来到篮下附近，突破继续往里走。",
            "这次进攻直指篮筐，动作还在延续。",
        ),
        required_any=("禁区", "篮下", "攻筐"),
    ),
    OriginalScenePhrase(
        id="drive_baseline",
        category="突破与终结",
        event_kinds=frozenset({"drive"}),
        phase="action",
        templates=(
            "持球人沿底线突破，正在从篮板后侧寻找角度。",
            "这一步压向底线，突破线路贴着边线展开。",
            "底线被打开，持球人顺势往篮下走。",
        ),
        required_any=("沿底线", "底线突破", "走底线"),
        min_confidence=0.76,
    ),
    OriginalScenePhrase(
        id="drive_spin",
        category="突破与终结",
        event_kinds=frozenset({"drive"}),
        phase="action",
        templates=(
            "一个转身，持球人继续向篮下压进去。",
            "转身护住篮球，突破线路重新打开。",
            "持球人用转身避开正面防守，动作还在延续。",
        ),
        required_any=("转身突破", "转身运球", "转身过人"),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="drive_eurostep",
        category="突破与终结",
        event_kinds=frozenset({"drive", "shot"}),
        phase="action",
        templates=(
            "欧洲步横向一跨，持球人避开了正面防守。",
            "两步改变方向，这个欧洲步把终结角度让了出来。",
            "持球人用欧洲步绕开防守，已经来到篮筐附近。",
        ),
        required_any=("欧洲步",),
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="drive_crossover",
        category="突破与终结",
        event_kinds=frozenset({"possession", "drive"}),
        phase="action",
        templates=(
            "一个交叉变向，持球方向突然改变。",
            "球从身前换手，这次变向把防守带开了。",
            "交叉运球接上突破，脚下节奏已经变了。",
        ),
        required_any=("交叉变向", "交叉运球", "体前变向"),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="drive_between_legs",
        category="突破与终结",
        event_kinds=frozenset({"possession", "drive"}),
        phase="action",
        templates=(
            "胯下换手以后继续向前，持球节奏没有断。",
            "一记胯下运球改变方向，防守需要重新移动。",
            "球从胯下完成换手，下一步突破随即接上。",
        ),
        required_any=("胯下运球", "胯下换手"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="drive_behind_back",
        category="突破与终结",
        event_kinds=frozenset({"possession", "drive"}),
        phase="action",
        templates=(
            "背后运球完成换手，持球人继续寻找路线。",
            "球从背后换到另一侧，防守重心被带动。",
            "一记背后运球护住球权，突破还在继续。",
        ),
        required_any=("背后运球", "背后换手"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="isolation_action",
        category="单打与背身",
        event_kinds=frozenset({"possession", "drive", "other"}),
        phase="reaction",
        templates=(
            "队友把空间拉开，持球人开始面框单打。",
            "这一侧留给持球人，一对一正面展开。",
            "进攻选择拉开单打，防守压力集中在持球点。",
        ),
        required_any=("面框单打", "拉开单打", "一对一单打", "持球单打"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="post_up_action",
        category="单打与背身",
        event_kinds=frozenset({"possession", "drive", "other"}),
        phase="action",
        templates=(
            "低位背身拿球，先用身体感受防守位置。",
            "持球人开始背身单打，脚步正在往篮下压。",
            "球给到低位，这次背打已经开始。",
        ),
        required_any=("低位背身", "背身单打", "低位背打", "背打"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="drive_skill_praise",
        category="现场夸赞",
        event_kinds=frozenset({"possession", "drive"}),
        phase="reaction",
        templates=(
            "这一步漂亮，持球人继续往篮下走。",
            "脚步真漂亮，方向一变还在往里走。",
            "这一下处理得干净，持球人继续往里走。",
            "好脚步！突破还在继续。",
        ),
        required_tags=(
            "crossover",
            "between_legs",
            "behind_back",
            "spin_move",
            "eurostep",
            "baseline_drive",
        ),
        is_praise=True,
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="shot_release",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "起来了，球已经离手。",
            "抬手就投，先看落点。",
            "机会一出来，抬手就投。",
            "球奔篮筐去了，先看落点。",
            "手一抬，球就离手了。",
            "这一下已经出手，跟着球看。",
        ),
        min_confidence=0.70,
    ),
    OriginalScenePhrase(
        id="shot_contested",
        category="防守与对位",
        event_kinds=frozenset({"shot"}),
        phase="reaction",
        templates=(
            "干扰已经来到面前，这次出手并不轻松。",
            "防守压力已经到位，投篮空间被压得很小。",
            "防守人在出手点前形成干扰，难度上来了。",
        ),
        required_any=("干扰", "扑防", "贴防"),
        min_confidence=0.72,
    ),
    OriginalScenePhrase(
        id="shot_three_point",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "三分出手！球已经从三分线外离开手中。",
            "人在三分线外起跳，这记三分已经出手。",
            "三分线外获得空间，抬手完成远投。",
        ),
        required_tags=("three_point",),
        requires_verified_tag=True,
        min_confidence=0.84,
    ),
    OriginalScenePhrase(
        id="shot_catch_and_shoot",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "接球就投，整个出手没有多余停顿。",
            "球到手马上起跳，这次接球投很果断。",
            "接球、起身、出手，动作衔接得很快。",
        ),
        required_any=("接球即投", "接球就投", "接球后立即出手"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="shot_spot_up",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "定点接球以后直接起跳，出手没有犹豫。",
            "空位定点机会出现，球已经离手。",
            "脚下先站稳，这次定点投篮顺势完成。",
        ),
        required_any=("定点投篮", "定点接球", "空位定点"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="shot_pullup",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "运球突然收住，急停跳投已经出手。",
            "急停、拔起，这记跳投来得很坚决。",
            "持球人用急停创造出空间，随即完成跳投。",
        ),
        required_any=("急停跳投", "运球急停", "急停出手"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="shot_jump",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "持球人拔起跳投，球已经离开手中。",
            "起跳以后完成出手，这记跳投动作很清楚。",
            "面对篮筐拔起，这次跳投已经完成。",
        ),
        required_any=("跳投",),
        min_confidence=0.76,
    ),
    OriginalScenePhrase(
        id="shot_stepback",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "后撤一步拉开空间，随即完成跳投。",
            "持球人用后撤步摆脱防守，投篮已经出手。",
            "脚步向后一收，这记后撤步跳投完成离手。",
        ),
        required_any=("后撤步",),
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="shot_fadeaway",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "身体向后拉开距离，后仰跳投已经出手。",
            "迎着防守后仰起跳，这次投篮完成离手。",
            "持球人用后仰创造空间，把球投了出去。",
        ),
        required_any=("后仰跳投", "后仰出手"),
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="shot_floater",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "抛投出手，球越过篮下防守飞向篮筐。",
            "持球人提前把球抛起，这记抛投已经离手。",
            "面对内线防守选择高抛，球正在飞向篮筐。",
        ),
        required_any=("抛投", "高抛"),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="shot_hook",
        category="投篮与出手",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "侧身把球勾向篮筐，这记勾手已经完成。",
            "持球人用勾手避开正面干扰，球已经离手。",
            "篮下转身接勾手，这次出手越过了防守。",
        ),
        required_any=("勾手", "跳勾"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="shot_layup",
        category="篮下终结",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "起步上篮，球已经从篮下送了出去。",
            "持球人跨出最后两步，上篮完成出手。",
            "人来到篮筐附近，这次上篮已经离手。",
        ),
        required_any=("上篮",),
        min_confidence=0.76,
    ),
    OriginalScenePhrase(
        id="shot_reverse_layup",
        category="篮下终结",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "从篮筐另一侧反篮出手，利用篮筐避开防守。",
            "持球人绕到篮板后侧，这记反篮已经送出。",
            "篮下换到另一边完成反篮，角度找得很巧。",
        ),
        required_any=("反篮", "反手上篮"),
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="shot_bank",
        category="篮下终结",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "选择擦板，球先奔着篮板而去。",
            "这次出手主动找篮板，擦板角度已经给出。",
            "球被送向篮板，这是一记清楚的打板出手。",
        ),
        required_any=("擦板", "打板"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="shot_dunk",
        category="篮下终结",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "人已经升到篮筐上方，准备完成扣篮。",
            "篮下直接起跳，这次扣篮动作已经展开。",
            "持球人强势起飞，篮球正被送向篮筐。",
        ),
        required_any=("扣篮", "灌篮"),
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="shot_putback",
        category="篮板与二次进攻",
        event_kinds=frozenset({"shot"}),
        phase="action",
        templates=(
            "篮下二次起跳，补篮马上接了上来。",
            "进攻篮板以后直接补篮，这一攻还在继续。",
            "第一点没有结束，紧接着完成补篮出手。",
        ),
        required_any=("补篮", "补扣", "二次起跳"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="shot_technique_praise",
        category="现场夸赞",
        event_kinds=frozenset({"shot"}),
        phase="reaction",
        templates=(
            "这一下处理得够果断，球已经离手。",
            "衔接很漂亮，这次出手随即完成。",
            "出手真坚决，球已经离手。",
            "这次终结的动作很顺，先看球的落点。",
        ),
        required_tags=(
            "catch_and_shoot",
            "pull_up",
            "step_back",
            "fadeaway",
            "floater",
            "hook_shot",
            "reverse_layup",
            "dunk",
            "putback",
            "alley_oop",
        ),
        is_praise=True,
        min_confidence=0.84,
    ),
    OriginalScenePhrase(
        id="made_generic",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "有了！",
            "进了！",
            "打进！",
            "命中！",
            "有了！这次机会把握住了。",
            "进了！这一球稳稳收下。",
            "命中！这一下处理得很干净。",
        ),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="made_praise",
        category="现场夸赞",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "打进！好球！",
            "命中！漂亮！",
            "有了！这一下把握得真稳！",
            "进了！机会没有浪费！",
            "打进！处理得干净利落！",
            "命中！这一下够果断！",
        ),
        is_praise=True,
        min_confidence=0.86,
    ),
    OriginalScenePhrase(
        id="made_tough_praise",
        category="现场夸赞",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "打进！顶着对抗也能收下，这球够硬！",
            "命中！身体接触以后还能稳稳收下！",
            "打进！强对抗下依然把球放进！",
        ),
        required_tags=("through_contact",),
        requires_verified_tag=True,
        is_praise=True,
        min_confidence=0.90,
    ),
    OriginalScenePhrase(
        id="made_contested_praise",
        category="现场夸赞",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "命中！面对干扰依然稳稳收下！",
            "打进！防守贴到面前，这球还是收下了！",
            "命中！干扰已经到位，依然稳稳收下！",
        ),
        required_tags=("contested_shot",),
        requires_verified_tag=True,
        is_praise=True,
        min_confidence=0.88,
    ),
    OriginalScenePhrase(
        id="made_net",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "命中！篮球清楚地穿网而过。",
            "打进！球已经落入篮筐。",
            "命中！这一球干净地通过篮网。",
            "打进！篮球稳稳落进篮筐。",
        ),
        required_any=("入网", "穿网", "空心", "落入篮筐", "落进篮筐"),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="made_three_point",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "命中！三分稳稳落袋。",
            "命中！这记三分球清楚地穿网而过。",
            "打进！这记三分稳稳入网。",
        ),
        required_tags=("three_point",),
        requires_verified_tag=True,
        min_confidence=0.84,
    ),
    OriginalScenePhrase(
        id="made_jump_shot",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "命中！这记跳投稳稳落袋。",
            "命中！这记跳投穿网而过。",
            "打进！这记跳投稳稳收下。",
        ),
        required_tags=("jump_shot", "pull_up", "step_back", "fadeaway"),
        requires_verified_tag=True,
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="made_layup",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "打进！上篮得手。",
            "命中！这次上篮稳稳放进。",
            "打进！篮下这记上篮完成得很扎实。",
        ),
        required_tags=("layup", "reverse_layup"),
        requires_verified_tag=True,
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="made_dunk",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "打进！扣篮得手！",
            "命中！篮球被直接扣进篮筐！",
            "打进！这记扣篮干净利落！",
        ),
        required_tags=("dunk", "alley_oop"),
        requires_verified_tag=True,
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="made_floater",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "命中！这记抛投柔和落袋。",
            "打进！高抛越过防守落进篮筐。",
            "命中！这记抛投轻轻落进篮筐。",
        ),
        required_tags=("floater",),
        requires_verified_tag=True,
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="made_hook_shot",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "命中！勾手柔和地落进篮筐。",
            "打进！这记勾手越过防守落进篮筐。",
            "命中！侧身勾手稳稳得手。",
        ),
        required_tags=("hook_shot",),
        requires_verified_tag=True,
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="made_bank_shot",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "命中！篮球擦板落进篮筐。",
            "打进！打板角度找得很准。",
            "命中！这记擦板轻轻落进篮筐。",
        ),
        required_tags=("bank_shot",),
        requires_verified_tag=True,
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="made_putback",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "打进！补篮得手，二次机会抓住了。",
            "命中！篮下的补篮稳稳收下。",
            "打进！二次起跳的补篮有了。",
        ),
        required_tags=("putback",),
        requires_verified_tag=True,
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="made_alley_oop",
        category="明确命中",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "打进！空中接力完成得干净利落！",
            "命中！空中连线稳稳送进篮筐！",
            "打进！这次空接在篮筐上方完成！",
        ),
        required_tags=("alley_oop",),
        requires_verified_tag=True,
        min_confidence=0.84,
    ),
    OriginalScenePhrase(
        id="missed_generic",
        category="明确未进",
        event_kinds=frozenset({"missed_shot"}),
        phase="result",
        templates=(
            "没进！",
            "没进！差一点。",
            "没进！可惜。",
            "没进！这一下没收住。",
            "没进！机会没抓住。",
        ),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="missed_rim",
        category="明确未进",
        event_kinds=frozenset({"missed_shot"}),
        phase="result",
        templates=(
            "没进！篮球从篮筐上弹了出来。",
            "没进！球碰到篮筐以后弹开。",
            "没进！球从篮筐边缘弹了出去。",
            "没进！篮球在篮筐处改变了方向。",
        ),
        required_any=("弹框", "弹筐", "打铁", "磕框", "磕筐", "涮筐"),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="block_generic",
        category="防守结果",
        event_kinds=frozenset({"block"}),
        phase="result",
        templates=(
            "盖到了！",
            "封盖！",
            "盖帽！这球被挡下来。",
            "盖到了！这一球没让它过去。",
            "封盖！进攻这一拍被按下来。",
        ),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="block_praise",
        category="现场夸赞",
        event_kinds=frozenset({"block"}),
        phase="result",
        templates=(
            "封盖！好帽！",
            "封盖！这一下防得真漂亮！",
            "盖帽！这次防守干净利落！",
            "封盖！篮下这一下守得真好！",
        ),
        is_praise=True,
        min_confidence=0.86,
    ),
    OriginalScenePhrase(
        id="block_emphatic",
        category="防守结果",
        event_kinds=frozenset({"block"}),
        phase="result",
        templates=(
            "封盖！这球结结实实吃了一记火锅！",
            "封盖！一记干净的大帽把球拦了下来！",
            "盖帽！这一下直接把进攻拒之门外！",
        ),
        required_any=("大帽", "钉板", "扇飞", "火锅", "强力封盖"),
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="steal_generic",
        category="防守结果",
        event_kinds=frozenset({"steal"}),
        phase="result",
        templates=(
            "断下来了！",
            "抢断！",
            "断球！球权换手。",
            "抢断！这一下把球拿住了。",
            "断下来了，回合方向变了！",
        ),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="steal_praise",
        category="现场夸赞",
        event_kinds=frozenset({"steal"}),
        phase="result",
        templates=(
            "抢断！断得漂亮！",
            "抢断！这一下抢得真准！",
            "断球！这一下切得干净！",
            "抢断！防守端把机会抓住了！",
        ),
        is_praise=True,
        min_confidence=0.86,
    ),
    OriginalScenePhrase(
        id="rebound_generic",
        category="篮板与二次进攻",
        event_kinds=frozenset({"rebound"}),
        phase="result",
        templates=(
            "篮板拿住！",
            "篮板到手！",
            "篮板！球权稳下来。",
            "篮板！这一下保护住了。",
            "篮板拿稳，回合接着打。",
        ),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="rebound_praise",
        category="现场夸赞",
        event_kinds=frozenset({"rebound"}),
        phase="result",
        templates=(
            "篮板！这一下保护得真稳！",
            "篮板！这个球拿得真稳！",
            "篮板！这个球权收得很扎实！",
        ),
        is_praise=True,
        min_confidence=0.86,
    ),
    OriginalScenePhrase(
        id="rebound_offensive",
        category="篮板与二次进攻",
        event_kinds=frozenset({"rebound"}),
        phase="reaction",
        templates=(
            "篮板！进攻方把第二次机会留了下来。",
            "篮板！这一攻还没有在这里结束。",
            "篮板！球权仍然留在进攻一侧。",
        ),
        required_any=("进攻篮板", "二次机会", "前场篮板"),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="rebound_boxout",
        category="篮板与二次进攻",
        event_kinds=frozenset({"rebound"}),
        phase="result",
        templates=(
            "篮板！先卡住位置，再把球稳稳保护下来。",
            "篮板！卡位到位，球权终于有了归属。",
            "篮板！防守方用卡位守住了这次落点。",
        ),
        required_any=("卡位", "保护篮板"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="transition_generic",
        category="攻守转换",
        event_kinds=frozenset({"transition"}),
        phase="action",
        templates=(
            "球权一换，速度马上起来。",
            "转换推起来了，球正在往前场走。",
            "拿住球就往前推，回合直接提速。",
            "方向变了，双方开始往前场跑。",
            "球往前给，转换没有停。",
            "攻守刚一换，推进马上接上。",
        ),
    ),
    OriginalScenePhrase(
        id="transition_fastbreak",
        category="攻守转换",
        event_kinds=frozenset({"transition"}),
        phase="action",
        templates=(
            "快攻已经推起来，防守还在回位。",
            "球权到手马上发动反击，速度一下提了上来。",
            "转换快攻没有停顿，进攻直接冲向前场。",
        ),
        required_any=("快攻", "反击"),
        min_confidence=0.76,
    ),
    OriginalScenePhrase(
        id="transition_coast_to_coast",
        category="攻守转换",
        event_kinds=frozenset({"transition", "drive"}),
        phase="reaction",
        templates=(
            "从后场一路推进到篮下，这次一条龙没有停。",
            "持球人贯穿全场，直接把反击带到篮下。",
            "球从后场一路向前，这次推进直奔篮筐。",
        ),
        required_any=("一条龙", "贯穿全场", "从后场一路"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="transition_praise",
        category="现场夸赞",
        event_kinds=frozenset({"transition"}),
        phase="reaction",
        templates=(
            "这次反击推得真快，场上速度一下起来了。",
            "这一波推进真漂亮，反击一路往前走。",
            "推得漂亮！球权一到手，速度马上提起来。",
            "这次向前处理得真果断，反击已经展开。",
        ),
        required_tags=("fast_break", "coast_to_coast", "outlet_pass"),
        is_praise=True,
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="transition_advantage",
        category="攻守转换",
        event_kinds=frozenset({"transition"}),
        phase="reaction",
        templates=(
            "前场人数占优，这次处理需要更快。",
            "转换形成多打少，眼前窗口不会停留太久。",
            "推进形成了人数优势，球要及时往前送。",
        ),
        required_any=("人数优势", "多打少", "人数占优"),
    ),
    OriginalScenePhrase(
        id="stoppage_generic",
        category="回合停顿",
        event_kinds=frozenset({"stoppage"}),
        phase="result",
        templates=(
            "比赛停下，场上节奏暂时慢了下来。",
            "回合中断，双方先等待比赛继续。",
            "比赛停止，现场节奏在这里停了一拍。",
            "回合停下，这一段攻防暂时告一段落。",
        ),
        min_confidence=0.78,
    ),
    OriginalScenePhrase(
        id="screen_action",
        category="掩护与挡拆",
        event_kinds=frozenset({"possession", "pass", "drive", "other"}),
        phase="reaction",
        templates=(
            "掩护已经出现，场上的进攻线路随之变化。",
            "进攻利用掩护移动，防守需要重新找位置。",
            "掩护开始展开，防守站位正在调整。",
            "掩护形成以后，进攻继续向空间里移动。",
        ),
        required_any=("掩护", "挡拆"),
        min_confidence=0.76,
    ),
    OriginalScenePhrase(
        id="off_ball_screen",
        category="掩护与挡拆",
        event_kinds=frozenset({"possession", "pass", "drive", "other"}),
        phase="reaction",
        templates=(
            "无球掩护在另一侧展开，接球空间开始出现。",
            "球还在强侧，弱侧已经用无球掩护跑动。",
            "这次掩护没有直接挡持球人，它在帮无球队友脱身。",
        ),
        required_any=("无球掩护", "给无球人掩护"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="pick_and_roll",
        category="掩护与挡拆",
        event_kinds=frozenset({"possession", "pass", "drive", "other"}),
        phase="reaction",
        templates=(
            "挡拆已经形成，掩护人随即顺下篮筐。",
            "持球人借挡拆向前，内线同时开始顺下。",
            "掩护以后直接顺下，这次挡拆衔接得很清楚。",
        ),
        required_all=("挡拆", "顺下"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="pick_and_pop",
        category="掩护与挡拆",
        event_kinds=frozenset({"possession", "pass", "drive", "other"}),
        phase="reaction",
        templates=(
            "挡拆以后没有顺下，掩护人转而外弹。",
            "掩护完成以后向外弹开，空间被重新拉大。",
            "这次挡拆选择外弹，外侧接球点已经出现。",
        ),
        required_all=("挡拆", "外弹"),
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="defensive_trap",
        category="防守与对位",
        event_kinds=frozenset({"possession", "pass", "drive", "other"}),
        phase="reaction",
        templates=(
            "两名防守人形成夹击，持球空间一下缩小。",
            "包夹已经合上，持球人需要尽快把球处理出去。",
            "防守夹击到位，原来的突破线路被封住。",
        ),
        required_any=("夹击", "包夹"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="help_defense",
        category="防守与对位",
        event_kinds=frozenset({"possession", "pass", "drive", "shot", "other"}),
        phase="reaction",
        templates=(
            "协防已经移动，进攻需要重新判断路线。",
            "协防人向球侧收过来，原来的空间正在变小。",
            "篮下协防已经到位，持球线路被进一步压缩。",
        ),
        required_any=("协防",),
        min_confidence=0.76,
    ),
    OriginalScenePhrase(
        id="defensive_rotation",
        category="防守与对位",
        event_kinds=frozenset({"possession", "pass", "drive", "shot", "other"}),
        phase="reaction",
        templates=(
            "防守轮转及时到位，原来的空间正在消失。",
            "防守人继续轮转，进攻需要再次转移。",
            "这一拍轮转已经跟上，空当没有停留太久。",
        ),
        required_any=("轮转",),
        min_confidence=0.76,
    ),
    OriginalScenePhrase(
        id="defensive_switch",
        category="防守与对位",
        event_kinds=frozenset({"possession", "pass", "drive", "shot", "other"}),
        phase="reaction",
        templates=(
            "换防完成，对位关系已经重新形成。",
            "防守选择换人跟防，新的对位已经接上。",
            "这次换防没有停顿，防守位置重新排好。",
        ),
        required_any=("换防",),
        min_confidence=0.76,
    ),
    OriginalScenePhrase(
        id="drop_coverage",
        category="防守与对位",
        event_kinds=frozenset({"possession", "drive", "other"}),
        phase="reaction",
        templates=(
            "内线选择沉退，先把篮下空间守住。",
            "挡拆防守没有扑上来，大个子在篮下沉退等待。",
            "防守向篮下沉退，中距离空间暂时被让了出来。",
        ),
        required_any=("沉退防守", "内线沉退", "挡拆沉退"),
        min_confidence=0.82,
    ),
    OriginalScenePhrase(
        id="rim_protection",
        category="防守与对位",
        event_kinds=frozenset({"shot", "other"}),
        phase="reaction",
        templates=(
            "篮下护框人已经到位，终结空间被压缩。",
            "内线守在篮筐附近，这次护框给到了压力。",
            "篮下的防守位置没有丢，护框线还在。",
        ),
        required_any=("护框", "守住篮下", "篮下封锁"),
        min_confidence=0.80,
    ),
    OriginalScenePhrase(
        id="critical_possession",
        category="可信关键背景",
        event_kinds=frozenset({"possession"}),
        phase="reaction",
        templates=(
            "时间压力已经到了，每一次处理都要更清楚。",
            "关键阶段的球权先稳住，再寻找真正的机会。",
            "比赛来到这个位置，这一攻需要耐心也需要果断。",
        ),
        min_confidence=0.74,
        requires_critical_context=True,
    ),
    OriginalScenePhrase(
        id="critical_shot",
        category="可信关键背景",
        event_kinds=frozenset({"shot"}),
        phase="reaction",
        templates=(
            "时间窗口已经很短，这次出手必须果断。",
            "关键阶段机会出现，球已经及时离手。",
            "倒计时继续向下，这一下出手没有犹豫。",
        ),
        min_confidence=0.74,
        requires_critical_context=True,
    ),
    OriginalScenePhrase(
        id="critical_made",
        category="可信关键背景",
        event_kinds=frozenset({"made_shot"}),
        phase="result",
        templates=(
            "命中！关键阶段稳稳收下这一球！",
            "打进！时间压力下依然把握住了！",
            "命中！关键时刻就是这样果断！",
        ),
        min_confidence=0.82,
        requires_critical_context=True,
    ),
    OriginalScenePhrase(
        id="critical_missed",
        category="可信关键背景",
        event_kinds=frozenset({"missed_shot"}),
        phase="result",
        templates=(
            "没进！关键阶段的一次遗憾。",
            "没进！时间还在继续往下走。",
            "没进！关键时刻没能把握住。",
        ),
        min_confidence=0.82,
        requires_critical_context=True,
    ),
)


def _event_value(event: object, key: str, default: object = "") -> object:
    if isinstance(event, MappingABC):
        return event.get(key, default)
    return getattr(event, key, default)


def _has_trusted_critical_context(
    trusted_context: str,
    game_context: Mapping[str, object] | None,
) -> bool:
    # A score by itself says nothing about whether this possession is late or
    # decisive.  Keep the argument for API compatibility, but require explicit
    # clock/period language in the trusted background before unlocking urgency.
    _ = game_context
    context = re.sub(r"\s+", "", trusted_context or "")
    if not context:
        return False
    return bool(
        re.search(r"(?:还剩|剩余|最后|倒计时)\d+(?:\.\d+)?(?:秒|分钟)", context)
        or re.search(r"(?:最后一攻|决胜阶段|决胜时刻)", context)
    )


def _scene_phrase_matches(
    phrase: OriginalScenePhrase,
    event: object,
    critical_context: bool,
) -> bool:
    kind = str(_event_value(event, "kind", "")).strip().lower()
    if kind not in phrase.event_kinds:
        return False
    try:
        confidence = float(_event_value(event, "confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        return False
    if confidence < phrase.min_confidence:
        return False
    if phrase.requires_critical_context and not critical_context:
        return False
    tag_source = (
        "verified_detail_tags" if phrase.requires_verified_tag else "detail_tags"
    )
    raw_tags = _event_value(event, tag_source, ())
    if isinstance(raw_tags, str):
        event_tags = {raw_tags.strip().lower()}
    elif isinstance(raw_tags, Sequence):
        event_tags = {
            str(tag).strip().lower()
            for tag in raw_tags
            if str(tag).strip()
        }
    else:
        event_tags = set()
    if phrase.required_tags and not any(
        tag.lower() in event_tags for tag in phrase.required_tags
    ):
        return False
    evidence = re.sub(
        r"\s+",
        "",
        f"{_event_value(event, 'action', '')}{_event_value(event, 'result', '')}",
    ).lower()
    if phrase.required_any and not any(
        keyword.lower() in evidence for keyword in phrase.required_any
    ):
        return False
    if phrase.required_all and not all(
        keyword.lower() in evidence for keyword in phrase.required_all
    ):
        return False
    return True


def _stable_template_offset(event_id: str, phrase_id: str, size: int) -> int:
    seed = f"{event_id}:{phrase_id}"
    return sum((index + 1) * ord(character) for index, character in enumerate(seed)) % size


class OriginalProfessionalBroadcastProfile:
    """Original text-and-delivery layer for an authorized recorded voice."""

    name = "broadcast_original"
    label = "原创专业篮球转播叙事"

    def planner_rules(self, duration: float) -> str:
        return f"""
原创专业篮球转播叙事层

方法
现场节奏永远先于背景信息。先说正在发生的动作，再用一句讲清空间、对位或战术因果；只有结果得到确认，情绪才到达峰值。信息储备要压成观众此刻用得上的关键词，不能为了“金句”离开比赛本身。

结构
普通回合优先使用“动作事实→防守变化→进攻选择→直接结果”。攻守转换可以连续两段短句提速，随后必须回到完整句。关键结果只爆发一次；若视频和用户信息足以支持，最后一段才允许一条克制的意义收束。{duration:.1f} 秒短片不写长篇生涯故事，也不虚构人物背景。

层次
主声层先交付球权、动作和结果；事件之间确有朗读空窗时，才补一条空间或防守因果。后续新动作一出现，尚未播出的解释立即让位给现场。术语首次出现要让普通观众听得懂，不能把战术、数据、互动和情绪四层同时塞进一句。

场景表达
具体表达候选会在音画事件确认后按 event_id 单独提供。没有被当前事件证据解锁的场景表达一律不可使用；候选只能择一改写，不能逐条照搬、连续套用或移动到其他事件。

边界
不得出现或暗示任何真实解说员姓名、身份、固定口头禅和标志性原句。不得声称真人参与配音。不得新增比分、人物经历、数据、队名、命中结果或判罚；没有可信数据时不做“数据翻译”，没有用户确认的背景时不做历史升华。
""".strip()

    def scene_hints(
        self,
        events: Sequence[object],
        *,
        trusted_context: str = "",
        game_context: Mapping[str, object] | None = None,
        per_event_limit: int = MAX_SCENE_HINTS_PER_EVENT,
        total_limit: int = MAX_SCENE_HINTS_TOTAL,
    ) -> str:
        """Return a small, evidence-matched subset of original scene phrases."""
        per_event_limit = max(0, min(MAX_SCENE_HINTS_PER_EVENT, per_event_limit))
        total_limit = max(0, min(MAX_SCENE_HINTS_TOTAL, total_limit))
        if not events or per_event_limit == 0 or total_limit == 0:
            return ""

        critical_context = _has_trusted_critical_context(
            trusted_context,
            game_context,
        )
        used_templates: set[str] = set()
        hint_lines: list[str] = []
        selected_total = 0
        praise_limit = max(1, min(4, (len(events) + 2) // 3))

        def normalized_event_id(event: object, event_index: int) -> str:
            raw_event_id = str(_event_value(event, "event_id", "") or "")
            event_id = re.sub(r"[^0-9A-Za-z_.-]", "", raw_event_id)[:32]
            return event_id or f"event{event_index + 1}"

        def phrase_priority(phrase: OriginalScenePhrase) -> tuple[object, ...]:
            return (
                phrase.requires_critical_context,
                phrase.requires_verified_tag,
                bool(phrase.required_tags),
                bool(phrase.required_all),
                bool(phrase.required_any),
                phrase.min_confidence,
            )

        praise_candidates: list[tuple[int, str, str, float]] = []
        for candidate_index, candidate_event in enumerate(events):
            matching_praise = any(
                phrase.is_praise
                and _scene_phrase_matches(
                    phrase,
                    candidate_event,
                    critical_context,
                )
                for phrase in ORIGINAL_SCENE_PHRASES
            )
            if not matching_praise:
                continue
            try:
                confidence = float(
                    _event_value(candidate_event, "confidence", 0.0) or 0.0
                )
            except (TypeError, ValueError):
                continue
            praise_candidates.append(
                (
                    candidate_index,
                    normalized_event_id(candidate_event, candidate_index),
                    str(_event_value(candidate_event, "kind", "")).lower(),
                    confidence,
                )
            )

        result_praise_kinds = {"made_shot", "block", "steal", "rebound"}
        result_candidates = sorted(
            (
                candidate
                for candidate in praise_candidates
                if candidate[2] in result_praise_kinds
            ),
            key=lambda candidate: (
                {"block": 4, "made_shot": 3, "steal": 2, "rebound": 1}.get(
                    candidate[2],
                    0,
                ),
                candidate[3],
                -candidate[0],
            ),
            reverse=True,
        )
        process_candidates = sorted(
            (
                candidate
                for candidate in praise_candidates
                if candidate[2] not in result_praise_kinds
            ),
            key=lambda candidate: (candidate[3], -candidate[0]),
            reverse=True,
        )
        selected_praise_candidates: list[tuple[int, str, str, float]] = []
        if result_candidates:
            selected_praise_candidates.append(result_candidates.pop(0))
        if process_candidates and len(selected_praise_candidates) < praise_limit:
            selected_praise_candidates.append(process_candidates.pop(0))
        remaining_candidates = sorted(
            result_candidates + process_candidates,
            key=lambda candidate: (candidate[3], -candidate[0]),
            reverse=True,
        )
        selected_praise_candidates.extend(
            remaining_candidates[
                : max(0, praise_limit - len(selected_praise_candidates))
            ]
        )
        praise_event_indexes = {
            candidate[0] for candidate in selected_praise_candidates
        }
        last_praise_signature = ""

        def praise_signature(template: str) -> str:
            for signature, pattern in (
                ("好球", r"好球"),
                ("漂亮", r"漂亮"),
                ("好帽", r"好帽"),
                ("好传", r"好传|传得真"),
                ("防得好", r"防得真好|守得真好"),
                ("稳", r"真稳|稳稳|扎实"),
                ("果断", r"果断|坚决"),
                ("干净", r"干净"),
            ):
                if re.search(pattern, template):
                    return signature
            return template[:8]

        for event_index, event in enumerate(events):
            if selected_total >= total_limit:
                break
            event_id = normalized_event_id(event, event_index)
            kind = str(_event_value(event, "kind", "")).strip().lower()
            matching = [
                phrase
                for phrase in ORIGINAL_SCENE_PHRASES
                if _scene_phrase_matches(phrase, event, critical_context)
            ]
            # Trusted critical context and explicitly observed tactical tags are
            # more useful than a generic line, but no family may contribute more
            # than one template to the same event.
            non_praise_matching = sorted(
                (phrase for phrase in matching if not phrase.is_praise),
                key=phrase_priority,
                reverse=True,
            )
            praise_matching = sorted(
                (phrase for phrase in matching if phrase.is_praise),
                key=phrase_priority,
                reverse=True,
            )
            matching = list(non_praise_matching)
            if event_index in praise_event_indexes and praise_matching:
                if matching:
                    matching = [matching[0], praise_matching[0], *matching[1:]]
                else:
                    matching = [praise_matching[0]]
            event_hints: list[str] = []
            for phrase in matching:
                if (
                    len(event_hints) >= per_event_limit
                    or selected_total >= total_limit
                ):
                    break
                offset = _stable_template_offset(
                    event_id,
                    phrase.id,
                    len(phrase.templates),
                )
                ordered_templates = (
                    phrase.templates[offset:] + phrase.templates[:offset]
                )
                unused_templates = [
                    candidate
                    for candidate in ordered_templates
                    if candidate not in used_templates
                ]
                if phrase.is_praise:
                    template = next(
                        (
                            candidate
                            for candidate in unused_templates
                            if praise_signature(candidate)
                            != last_praise_signature
                        ),
                        unused_templates[0] if unused_templates else "",
                    )
                else:
                    template = unused_templates[0] if unused_templates else ""
                if not template:
                    continue
                used_templates.add(template)
                event_hints.append(template)
                selected_total += 1
                if phrase.is_praise:
                    last_praise_signature = praise_signature(template)
            if event_hints:
                hint_lines.append(
                    f"- {event_id}（{kind}）：{'／'.join(event_hints)}"
                )

        if not hint_lines:
            return ""
        return (
            "原创场景表达候选\n"
            "以下候选已经按事件类型、画面文字证据和置信度筛选。每条只绑定标注的 event_id，"
            "最多择一改写；不得照搬全部候选，不得跨事件使用，也不得借候选新增画面事实。\n"
            + "\n".join(hint_lines)
        )

    def rewrite_rules(self) -> str:
        return (
            "按原创专业转播方式修订：优先补清动作之间的因果和防守关系，"
            "删掉脱离现场的空泛抒情。常态用完整口语句，转换阶段最多连续两条短句，"
            "结果确认后只设一个峰值，再用一句落回比赛。表达库只作改写参考，不能机械套句，"
            "也不得加入任何真人解说员姓名、口头禅、标志性原句或未经证实的背景。"
        )

    def tts_instruction(self, style: str) -> str:
        energy = {
            "hype": "动作连续时明显提速，确认关键结果时短促爆发一次，随即回落。",
            "pro": "判断克制，战术关系说清楚，关键结果只轻微抬高一次。",
            "fun": "语气亲近自然，但仍保持专业判断，普通回合不要硬喊。",
        }.get(style, "动作时自然提速，确认结果后及时收住。")
        return (
            "已授权AI合成音色，专业电视篮球转播口吻。现场优先，像真实看球时即时接话，"
            "完整句与动作短句交替，保留自然呼吸，不要播音、朗诵或客服腔。"
            f"{energy}不得模仿任何真实人物。"
        )

    def compact_tts_instruction(self, style: str) -> str:
        energy = {
            "hype": "动作时提速，结果只爆发一次后回落",
            "pro": "判断克制，讲清攻防，结果轻抬后收住",
            "fun": "自然亲近，动作及时反应，普通回合不硬喊",
        }.get(style, "动作时提速，结果后收住")
        return (
            f"已授权AI合成音色，专业篮球现场转播。{energy}；"
            "完整句和短句交替，自然呼吸，不要播音腔，不模仿真人。"
        )


ORIGINAL_PROFESSIONAL_BROADCAST = OriginalProfessionalBroadcastProfile()
