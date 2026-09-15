# WuWa Local Tracker

A fully local, offline gacha history tracker for **Wuthering Waves**.

No external servers. No data collection. Your pull history stays on your machine.

---

## Why?

Most gacha trackers require you to paste your Convene URL into a website, trusting a third party with your account data. Some have even been caught [distributing malware](https://www.reddit.com/r/WutheringWaves/).

This tracker runs **100% locally**:
- Reads your game log to extract the Convene URL
- Fetches records directly from Kuro Games' official API
- Saves everything to a local JSON file
- Viewer runs in your browser with no network requests

## Files

| File | Description |
|------|-------------|
| `Run-Tracker.bat` | **Double-click this to run.** Fetches your gacha records. |
| `WuWa-LocalTracker.ps1` | PowerShell script (called by the bat file) |
| `WuWa-Viewer.html` | Open in browser, drag & drop JSON to view stats |

## How to Use

### Step 1: Fetch your records

1. Launch Wuthering Waves
2. Open **Convene History** in-game (this generates the URL in logs)
3. Close the history screen
4. **Double-click `Run-Tracker.bat`**

The script will:
- Auto-detect your game installation (Kuro client, Steam, Epic)
- Extract the Convene URL from game logs
- Fetch all banner records from the official API
- Save to `wuwa_pulls_<your_player_id>.json`

### Step 2: View your stats

1. Open `WuWa-Viewer.html` in any browser
2. Drag & drop the JSON file onto the page

You'll see:
- **Pity counter** per banner (with progress bar)
- **5★ history** with pull count per 5★
- **Statistics**: total pulls, 5★/4★ rate, average pity

### Data Merging

Every time you run the tracker, it **merges** new records with your existing JSON. This means:
- Records older than 6 months (expired from Kuro's API) are preserved locally
- You never lose data — just run the tracker periodically

## Supported Installations

- Kuro Games Launcher (default path)
- Steam
- Epic Games Store
- Custom install paths (scans all drives)

## Security

This project exists because we don't trust third-party trackers. So you shouldn't have to trust us either.

**Read the code yourself.** The PowerShell script is ~400 lines, fully commented.

What the script does:
- ✅ Reads game log files (Client.log, debug.log)
- ✅ Sends requests to Kuro Games' official gacha API
- ✅ Saves JSON to the same folder as the script
- ❌ No external servers contacted
- ❌ No telemetry or analytics
- ❌ No data uploaded anywhere

## Pity System Reference

| Banner | Pity (5★) | Guarantee |
|--------|-----------|-----------|
| Featured Resonator | 80 | 160 (50/50 → guaranteed) |
| Featured Weapon | 80 | — |
| Standard Resonator | 80 | — |
| Standard Weapon | 80 | — |
| Beginner | 50 | — |
| Beginners Choice | 80 | — |

## Requirements

- Windows 10/11
- PowerShell 5.1+ (included with Windows)
- Wuthering Waves installed

## Troubleshooting

**"Could not find Convene URL"**
→ Launch the game and open Convene History first. The URL is only written to logs when you view the history in-game.

**"Could not find game path"**
→ If installed in a non-standard location, the script scans all drives. Make sure the game has been launched at least once.

**JSON save error**
→ Make sure the script folder is not read-only (e.g. don't run from inside a zip file).

---

## 한국어 안내

명조 가챠 기록을 **완전히 로컬에서** 추적하는 도구입니다.

### 사용법

1. 명조 실행 → 소집 기록(Convene History) 열기 → 닫기
2. `Run-Tracker.bat` 더블클릭
3. `WuWa-Viewer.html`을 브라우저에서 열고 JSON 파일 드래그

### 특징

- 외부 서버 전송 **없음** — 쿠로 공식 API에서만 데이터 수집
- 6개월 지나 만료된 기록도 로컬에 보존 (자동 병합)
- 배너별 천장 카운터, 5성 히스토리, 확률 통계 제공

---

## License

MIT License — free to use, modify, and distribute.
