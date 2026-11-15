"""
Card Overlay Generator for Motion Video Agent.
Renders broadcast-quality Social Media Cards:
- X / Twitter Post Card (with real Twitter Blue Verified Badge)
- Reddit Narrative Post Card (with real Reddit Snoo Logo)
- Instagram Reel Hook Card (with real Instagram Logo)
- YouTube Comment / Superchat Card (with real YouTube Play Logo)
All rendered with anti-aliasing, clean typography, dynamic sizing, and alpha transparency.
"""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import os


class CardOverlayGenerator:
    """Generates broadcast-quality transparent PNG overlay cards for video composition."""

    @staticmethod
    def _get_font(font_size: int, bold: bool = False) -> ImageFont.ImageFont:
        """Attempts to load a standard system or clean font, falling back safely."""
        candidate_fonts = [
            "C:/Windows/Fonts/segoeui.ttf" if not bold else "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arial.ttf" if not bold else "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibri.ttf" if not bold else "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/tahoma.ttf" if not bold else "C:/Windows/Fonts/tahomabd.ttf",
        ]
        for fpath in candidate_fonts:
            if os.path.exists(fpath):
                try:
                    return ImageFont.truetype(fpath, font_size)
                except Exception:
                    continue
        return ImageFont.load_default()

    @staticmethod
    def _load_logo(logo_name: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        """Loads a real logo asset from disk and resizes with high-quality antialiasing."""
        candidates = [
            Path("backend/app/assets/logos") / logo_name,
            Path("frontend/public/logos") / logo_name,
            Path("app/assets/logos") / logo_name,
        ]
        for p in candidates:
            if p.exists():
                try:
                    img = Image.open(str(p.resolve())).convert("RGBA")
                    return img.resize(size, Image.Resampling.LANCZOS)
                except Exception:
                    pass
        return None

    @classmethod
    def generate_tweet_card(
        cls,
        author_name: str = "Peak Heist Clips",
        handle: str = "@peakheistclips",
        tweet_text: str = "Every soldier gets asked the same question at least once: 'what breathing technique do you use on long runs?'",
        output_path: str = "tweet_card.png",
        canvas_width: int = 1080,
        card_width: int = 960,
        bg_color: Tuple[int, int, int, int] = (14, 20, 27, 245),
        text_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> str:
        """Renders an authentic X / Twitter post card with real blue verified badge."""
        font_name = cls._get_font(34, bold=True)
        font_handle = cls._get_font(26, bold=False)
        font_body = cls._get_font(36, bold=False)

        words = tweet_text.split()
        lines = []
        cur_line = []
        max_text_w = card_width - 80

        dummy_img = Image.new("RGBA", (10, 10))
        dummy_draw = ImageDraw.Draw(dummy_img)

        for w in words:
            test_line = " ".join(cur_line + [w])
            bbox = dummy_draw.textbbox((0, 0), test_line, font=font_body)
            if bbox[2] - bbox[0] > max_text_w and cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        line_height = 50
        body_height = len(lines) * line_height
        header_height = 120
        total_card_h = header_height + body_height + 40

        card_img = Image.new("RGBA", (card_width, total_card_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card_img)

        # Rounded card background
        draw.rounded_rectangle(
            [(0, 0), (card_width, total_card_h)],
            radius=24,
            fill=bg_color,
            outline=(255, 255, 255, 40),
            width=2,
        )

        # Avatar circle
        avatar_r = 38
        avatar_cx = 40 + avatar_r
        avatar_cy = 30 + avatar_r
        draw.ellipse(
            [(avatar_cx - avatar_r, avatar_cy - avatar_r), (avatar_cx + avatar_r, avatar_cy + avatar_r)],
            fill=(29, 155, 240, 255),
            outline=(255, 255, 255, 120),
            width=2,
        )
        initial = (author_name[0] if author_name else "X").upper()
        font_init = cls._get_font(38, bold=True)
        ibox = draw.textbbox((0, 0), initial, font=font_init)
        draw.text((avatar_cx - (ibox[2] - ibox[0]) / 2, avatar_cy - (ibox[3] - ibox[1]) / 2 - 4), initial, font=font_init, fill=(255, 255, 255, 255))

        # Author Name
        name_x = avatar_cx + avatar_r + 20
        name_y = 35
        draw.text((name_x, name_y), author_name, font=font_name, fill=text_color)
        nbox = draw.textbbox((name_x, name_y), author_name, font=font_name)

        # Real Twitter Verified Blue Badge
        badge_size = 28
        logo = cls._load_logo("twitter_verified.png", (badge_size, badge_size))
        if logo:
            card_img.paste(logo, (nbox[2] + 12, name_y + 4), logo)
        else:
            badge_x = nbox[2] + 12
            badge_y = name_y + 6
            draw.ellipse([(badge_x, badge_y), (badge_x + badge_size, badge_y + badge_size)], fill=(29, 155, 240, 255))
            draw.line([(badge_x + 6, badge_y + 13), (badge_x + 11, badge_y + 18), (badge_x + 20, badge_y + 8)], fill=(255, 255, 255, 255), width=3)

        # Handle (@handle)
        draw.text((name_x, name_y + 42), handle, font=font_handle, fill=(160, 175, 185, 255))

        # Body text lines
        cur_y = 135
        for line in lines:
            draw.text((40, cur_y), line, font=font_body, fill=(245, 245, 245, 255))
            cur_y += line_height

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        card_img.save(str(out_path), format="PNG")
        return str(out_path)

    @classmethod
    def generate_reddit_hook_card(
        cls,
        subreddit: str = "r/technology",
        author_name: str = "u/example",
        question_text: str = "What happens when AI changes everything? The biggest shift might not be the technology itself, but how we use it.",
        upvotes: str = "2.4k",
        comments_count: str = "183",
        output_path: str = "reddit_card.png",
        card_width: int = 940,
    ) -> str:
        """Renders an authentic Reddit card with the real Reddit Snoo logo."""
        font_sub = cls._get_font(26, bold=True)
        font_meta = cls._get_font(22, bold=False)
        font_title = cls._get_font(34, bold=True)
        font_badge = cls._get_font(22, bold=True)

        words = question_text.split()
        lines = []
        cur_line = []
        max_text_w = card_width - 80

        dummy_img = Image.new("RGBA", (10, 10))
        dummy_draw = ImageDraw.Draw(dummy_img)

        for w in words:
            test_line = " ".join(cur_line + [w])
            bbox = dummy_draw.textbbox((0, 0), test_line, font=font_title)
            if bbox[2] - bbox[0] > max_text_w and cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        line_h = 46
        body_h = len(lines) * line_h
        total_card_h = 100 + body_h + 50

        card_img = Image.new("RGBA", (card_width + 8, total_card_h + 8), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card_img)

        # Soft drop shadow
        draw.rounded_rectangle([(6, 6), (card_width + 6, total_card_h + 6)], radius=20, fill=(15, 17, 21, 230))

        # Main surface with rounded corners
        draw.rounded_rectangle([(0, 0), (card_width, total_card_h)], radius=20, fill=(255, 255, 255, 250), outline=(230, 230, 230, 255), width=2)

        # Real Reddit Snoo Logo
        logo = cls._load_logo("reddit_logo.png", (48, 48))
        if logo:
            card_img.paste(logo, (35, 22), logo)
        else:
            draw.ellipse([(35, 25), (75, 65)], fill=(255, 69, 0, 255))
            draw.text((46, 28), "r/", font=font_sub, fill=(255, 255, 255, 255))

        # Subreddit title & author
        draw.text((95, 22), subreddit, font=font_sub, fill=(20, 20, 20, 255))
        draw.text((95, 52), f"{author_name} • 2 hours ago", font=font_meta, fill=(110, 110, 110, 255))

        # Question text
        cur_y = 92
        for line in lines:
            draw.text((35, cur_y), line, font=font_title, fill=(20, 20, 20, 255))
            cur_y += line_h

        # Footer telemetry strip: upvotes + comments
        foot_y = total_card_h - 40
        draw.line([(35, foot_y - 10), (card_width - 35, foot_y - 10)], fill=(235, 235, 235, 255), width=1)
        draw.text((35, foot_y), f"↑ {upvotes} • {comments_count} comments", font=font_badge, fill=(120, 120, 120, 255))

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        card_img.save(str(out_path), format="PNG")
        return str(out_path)

    @classmethod
    def generate_instagram_card(
        cls,
        author_name: str = "creator_hub",
        handle: str = "@creator_hub",
        hook_text: str = "The #1 secret high-performing creators use to get 10M+ views consistently.",
        output_path: str = "instagram_card.png",
        card_width: int = 940,
    ) -> str:
        """Renders an authentic Instagram Reel Hook Card with the real Instagram Logo."""
        font_handle = cls._get_font(28, bold=True)
        font_body = cls._get_font(34, bold=False)
        font_action = cls._get_font(22, bold=True)

        words = hook_text.split()
        lines = []
        cur_line = []
        max_text_w = card_width - 80

        dummy_img = Image.new("RGBA", (10, 10))
        dummy_draw = ImageDraw.Draw(dummy_img)

        for w in words:
            test_line = " ".join(cur_line + [w])
            bbox = dummy_draw.textbbox((0, 0), test_line, font=font_body)
            if bbox[2] - bbox[0] > max_text_w and cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        line_h = 46
        body_h = len(lines) * line_h
        total_card_h = 100 + body_h + 50

        card_img = Image.new("RGBA", (card_width, total_card_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card_img)

        # Dark sleek surface with subtle border
        draw.rounded_rectangle([(0, 0), (card_width, total_card_h)], radius=22, fill=(18, 18, 20, 245), outline=(255, 255, 255, 30), width=1)

        # Real Instagram Logo
        logo = cls._load_logo("instagram_logo.png", (48, 48))
        if logo:
            card_img.paste(logo, (32, 22), logo)
        else:
            draw.rounded_rectangle([(32, 22), (80, 70)], radius=12, fill=(225, 48, 108, 255))

        # Handle + Follow pill
        draw.text((95, 30), handle, font=font_handle, fill=(255, 255, 255, 255))
        # Follow button
        draw.rounded_rectangle([(card_width - 140, 24), (card_width - 35, 62)], radius=10, fill=(0, 149, 246, 255))
        font_btn = cls._get_font(20, bold=True)
        draw.text((card_width - 110, 32), "Follow", font=font_btn, fill=(255, 255, 255, 255))

        # Hook Text
        cur_y = 90
        for line in lines:
            draw.text((32, cur_y), line, font=font_body, fill=(245, 245, 245, 255))
            cur_y += line_h

        # Action bar
        foot_y = total_card_h - 38
        draw.line([(32, foot_y - 8), (card_width - 32, foot_y - 8)], fill=(45, 45, 50, 255), width=1)
        draw.text((32, foot_y), "❤️ 184K   💬 2,410   ✈ Share", font=font_action, fill=(180, 180, 190, 255))

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        card_img.save(str(out_path), format="PNG")
        return str(out_path)

    @classmethod
    def generate_comment_card(
        cls,
        author_name: str = "Creator Fan",
        badge_text: str = "CA$ 14.99 SUPERCHAT",
        comment_text: str = "If you produce 10 shorts daily with AI, what happens to channel velocity?",
        output_path: str = "comment_card.png",
        card_width: int = 880,
    ) -> str:
        """Renders an authentic YouTube Superchat / Comment card with the real YouTube Logo."""
        font_author = cls._get_font(28, bold=True)
        font_badge = cls._get_font(22, bold=True)
        font_body = cls._get_font(32, bold=False)

        words = comment_text.split()
        lines = []
        cur_line = []
        max_text_w = card_width - 80

        dummy_img = Image.new("RGBA", (10, 10))
        dummy_draw = ImageDraw.Draw(dummy_img)

        for w in words:
            test_line = " ".join(cur_line + [w])
            bbox = dummy_draw.textbbox((0, 0), test_line, font=font_body)
            if bbox[2] - bbox[0] > max_text_w and cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        line_h = 44
        body_h = len(lines) * line_h
        total_card_h = 100 + body_h + 35

        card_img = Image.new("RGBA", (card_width, total_card_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card_img)

        # Superchat vibrant container
        draw.rounded_rectangle(
            [(0, 0), (card_width, total_card_h)],
            radius=20,
            fill=(26, 115, 232, 245),
            outline=(255, 255, 255, 80),
            width=2,
        )

        # Real YouTube Logo
        logo = cls._load_logo("youtube_logo.png", (48, 48))
        if logo:
            card_img.paste(logo, (30, 22), logo)
        else:
            draw.ellipse([(30, 22), (78, 70)], fill=(255, 0, 0, 255))

        # Author Name
        name_x = 92
        name_y = 28
        draw.text((name_x, name_y), author_name, font=font_author, fill=(255, 255, 255, 255))
        nbox = draw.textbbox((name_x, name_y), author_name, font=font_author)

        # Currency Superchat pill
        if badge_text:
            badge_x = nbox[2] + 16
            draw.rounded_rectangle([(badge_x - 8, name_y - 2), (badge_x + 230, name_y + 32)], radius=8, fill=(0, 226, 151, 255))
            draw.text((badge_x, name_y + 3), badge_text, font=font_badge, fill=(15, 30, 20, 255))

        # Comment text
        cur_y = 92
        for line in lines:
            draw.text((32, cur_y), line, font=font_body, fill=(255, 255, 255, 255))
            cur_y += line_h

        out_path = Path(output_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        card_img.save(str(out_path), format="PNG")
        return str(out_path)
