import threading
from urllib.parse import urlparse
import flet as ft
import flet_audio as fta
import yt_dlp


def is_safe_url(url: str) -> bool:
    """Проверяет, что ссылка использует безопасный протокол HTTPS."""
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and bool(parsed.netloc)
    except Exception:
        return False


def main(page: ft.Page):
    page.title = "YT Music Android"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#030303"
    page.padding = 15

    # Инициализация без обращения к сторонним сайтам при запуске
    audio_player = fta.Audio(autoplay=False)
    page.overlay.append(audio_player)

    is_playing = False
    is_busy = False  # Защита от спама потоками (Race Condition / Rate Limit)

    status_text = ft.Text(
        "Выберите трек",
        size=14,
        weight=ft.FontWeight.BOLD,
        color="white",
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
    )
    results_list = ft.ListView(expand=True, spacing=8)
    search_input = ft.TextField(
        hint_text="Поиск песен или артистов...",
        max_length=100,  # Ограничение длины запроса
        expand=True,
        bgcolor="#1a1a1a",
        border_radius=8,
        border_color="transparent",
        on_submit=lambda e: search_music(e),
    )

    def search_music(e):
        nonlocal is_busy
        query = (search_input.value or "").strip()
        if not query or is_busy:
            return

        is_busy = True
        status_text.value = "⏳ Поиск треков..."
        results_list.controls.clear()
        page.update()
        threading.Thread(
            target=fetch_results, args=(query,), daemon=True
        ).start()

    def fetch_results(query):
        nonlocal is_busy
        ydl_opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "quiet": True,
            "extract_flat": True,
            "socket_timeout": 10,  # Таймаут для защиты от зависания сети
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch15:{query}", download=False)
                tracks = info.get("entries", [])

            results_list.controls.clear()
            for t in tracks:
                if not t:
                    continue
                title = t.get("title", "Без названия")
                video_id = t.get("id")
                url = t.get("url") or (
                    f"https://www.youtube.com/watch?v={video_id}"
                    if video_id
                    else ""
                )

                if not is_safe_url(url):
                    continue

                duration = t.get("duration")
                dur_str = (
                    f"{int(duration // 60)}:{int(duration % 60):02d}"
                    if isinstance(duration, (int, float))
                    else ""
                )

                results_list.controls.append(
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(
                                ft.Icons.MUSIC_NOTE, color="#ff0000"
                            ),
                            title=ft.Text(
                                title,
                                color="white",
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            trailing=ft.Text(dur_str, color="grey", size=12),
                            on_click=lambda e, u=url, ti=title: play_track(
                                u, ti
                            ),
                        ),
                        bgcolor="#121212",
                        border_radius=8,
                    )
                )
            status_text.value = "Выберите трек для воспроизведения"
        except Exception:
            status_text.value = (
                "Не удалось выполнить поиск. Проверьте подключение к сети."
            )
        finally:
            is_busy = False
            page.update()

    def play_track(url, title):
        nonlocal is_busy
        if is_busy or not is_safe_url(url):
            return

        is_busy = True
        status_text.value = f"⏳ Загрузка потока: {title}"
        page.update()
        threading.Thread(
            target=stream_audio, args=(url, title), daemon=True
        ).start()

    def stream_audio(url, title):
        nonlocal is_playing, is_busy
        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio",
            "quiet": True,
            "noplaylist": True,
            "socket_timeout": 10,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                stream_url = info.get("url", "")

            if not is_safe_url(stream_url):
                raise ValueError("Некорректный URL аудиопотока")

            audio_player.src = stream_url
            audio_player.autoplay = True
            audio_player.update()

            is_playing = True
            play_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED
            status_text.value = f"🎵 {title}"
        except Exception:
            status_text.value = "Не удалось воспроизвести этот трек."
        finally:
            is_busy = False
            page.update()

    def toggle_play(e):
        nonlocal is_playing
        if not audio_player.src:
            return
        if is_playing:
            audio_player.pause()
            play_btn.icon = ft.Icons.PLAY_CIRCLE_FILLED
            is_playing = False
        else:
            audio_player.resume()
            play_btn.icon = ft.Icons.PAUSE_CIRCLE_FILLED
            is_playing = True
        page.update()

    play_btn = ft.IconButton(
        icon=ft.Icons.PLAY_CIRCLE_FILLED,
        icon_size=42,
        icon_color="#ff0000",
        on_click=toggle_play,
    )

    search_bar = ft.Row(
        [
            search_input,
            ft.IconButton(
                icon=ft.Icons.SEARCH,
                icon_color="white",
                bgcolor="#ff0000",
                on_click=search_music,
            ),
        ]
    )

    player_bar = ft.Container(
        content=ft.Row(
            [ft.Container(content=status_text, expand=True), play_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        bgcolor="#181818",
        padding=ft.padding.symmetric(horizontal=15, vertical=8),
        border_radius=12,
    )

    page.add(
        search_bar,
        ft.Divider(color="transparent", height=5),
        results_list,
        player_bar,
    )


ft.app(target=main)
