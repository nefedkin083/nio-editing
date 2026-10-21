# NIO Editing

A skill for AI agents: turns raw phone footage into a short vertical reel in NIO's style — only the
strongest action, a hook-and-return story, cuts that enter late on the action, live sound, optional
cut-to-the-beat music.

Скилл для AI-агента: из сырых видео с телефона собирает короткий вертикальный ролик в стиле NIO —
только самый экшн, рамка «кульминация в начале и возврат в конце», склейки сразу на действии,
живой звук, по желанию монтаж под музыку в долю.

## Установка

Скажи своему агенту:

> Установи скилл монтажа из https://github.com/nefedkin083/nio-editing

Агент клонирует репозиторий в свою папку скиллов (например, `.claude/skills/nio-editing`),
ставит зависимости и попросит ключи. Перед каждым монтажом скилл сам подтягивает последнюю версию,
обновления приходят автоматически.

Вручную:

```bash
git clone https://github.com/nefedkin083/nio-editing ~/.claude/skills/nio-editing
pip install --user -r ~/.claude/skills/nio-editing/requirements.txt
```

## Что нужно

- `ffmpeg` с поддержкой `zscale` (для HDR-видео с iPhone).
- Ключ Gemini: `GEMINI_API_KEY` из [Google AI Studio](https://aistudio.google.com/apikey)
  или сервисный аккаунт Vertex AI (`GOOGLE_APPLICATION_CREDENTIALS`).
- По желанию `DEEPGRAM_API_KEY`, чтобы точно резать реплики по словам.

Стоимость: примерно $2–3 на 30–40 минут исходников. Ключи и деньги у каждого свои,
скилл ничего никуда не отправляет, кроме прокси-видео в Gemini.

## Как пользоваться

Скинь агенту видео (или ссылку на папку) и скажи: «смонтируй ролик». Можно уточнить:
«только треш», «под этот трек», «короче», «конец на разбитом стекле».

Весь метод описан в [SKILL.md](SKILL.md).

## License

MIT
