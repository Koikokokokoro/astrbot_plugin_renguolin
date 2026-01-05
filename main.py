import os
import random
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("任国林语录", "rglQuotation", "自己看书", "0.1.0")
class RGL(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
        except Exception:
            base_dir = os.getcwd()
        self.quation_path = os.path.join(base_dir, "quation.txt")
        self.replies = self._load_replies()

    def _load_replies(self):
        """读取 quation.txt：
           - 普通非空行视为一条回复
           - 花括号 { ... } 包裹的多行（或单行）视为一条回复（保留内部换行）
        """
        default = [
            "没有内容，自己想"
        ]

        if not os.path.exists(self.quation_path):
            logger.warning(f"没有内容，自己想。期望路径: {self.quation_path}")
            return default

        entries = []
        try:
            with open(self.quation_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            in_block = False
            block_lines = []
            for raw in lines:
                line = raw.rstrip("\n")
                # check for block start/end on same line: { ... }
                if not in_block:
                    # strip leading/trailing spaces to check for a lone '{'
                    stripped = line.strip()
                    # start of block with possible content after '{'
                    if "{" in stripped:
                        # find first '{'
                        start_idx = stripped.find("{")
                        after = stripped[start_idx+1:]
                        # check if '}' also on same line
                        if "}" in after:
                            end_idx = after.find("}")
                            content = after[:end_idx].strip()
                            if content:
                                entries.append(content)
                            else:
                                # empty block -> ignore
                                pass
                            # continue without changing in_block
                        else:
                            # start multi-line block
                            in_block = True
                            # anything after '{' on same line counts as first block line
                            if after.strip():
                                block_lines.append(after)
                    else:
                        # not a block line; treat as normal entry if non-empty
                        if stripped != "":
                            entries.append(stripped)
                else:
                    # currently inside block, look for closing '}'
                    if "}" in line:
                        # take content before first '}'
                        idx = line.find("}")
                        before = line[:idx]
                        if before != "":
                            block_lines.append(before)
                        # join block lines preserving internal newlines
                        entry = "\n".join([ln.rstrip() for ln in block_lines]).strip()
                        if entry:
                            entries.append(entry)
                        # reset block state
                        in_block = False
                        block_lines = []
                        # if there's text after '}', ignore it (alternatively could parse more)
                    else:
                        block_lines.append(line)
            # If file ends while still in block, finalize it anyway
            if in_block and block_lines:
                entry = "\n".join([ln.rstrip() for ln in block_lines]).strip()
                if entry:
                    entries.append(entry)

            if not entries:
                logger.warning(f"没有内容，自己想。路径: {self.quation_path}")
                return default

            return entries

        except Exception as e:
            logger.error(f"加载 quation.txt 时出错: {e}")
            return default

    @filter.command("ren")
    async def ren(self, event: AstrMessageEvent):
        """
        /ren —— 随机从 quation.txt 中读取并回复一句。
        如果希望每次都实时读取文件（支持热更新），可以取消下面注释来每次调用时重新加载：
            self.replies = self._load_replies()
        """
        # 每次实时加载可以开启下一行（按需）：
        # self.replies = self._load_replies()
        reply = random.choice(self.replies)
        yield event.plain_result(reply)