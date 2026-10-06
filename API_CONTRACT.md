# nuvra API Contract (v1)

> **Source of truth for every endpoint.** Server routes live in `backend/apps/*/urls.py`;
> the Flutter client maps them in `lib/data/api/`. Any endpoint change updates this file
> in the same commit (STANDARDS.md §7).
>
> Base URL: `http://10.0.2.2:8000/api/v1` (Android emulator) · LAN `http://<pc-ip>:8000/api/v1` · prod `https://<host>/api/v1`
>
> Auth: `Authorization: Bearer <access>` (JWT, 30-min access / 30-day refresh, rotation on).
> Every error: `{ "detail": "<human>", "code": "<machine>" }`.

---

## Public (no auth)

| Method | Path | Body/Query | Returns |
|---|---|---|---|
| GET | `/health` | — | `{status, database}` (200 or 503) |
| GET | `/config` | — | `{min_app_version, maintenance_mode, service_fee_percent, categories, enums{...}, moderation{hard_reason, soft_reason}}` |
| POST | `/auth/otp/request` | `{email}` | `{sent: bool, cooldown_seconds: int}` — no account enumeration; dev demo code `424242` |
| POST | `/auth/otp/verify` | `{email, code}` | `{access, refresh, member{...}, profile_completed: bool}` |
| POST | `/auth/refresh` | `{refresh}` | `{access, refresh}` (rotation; old refresh blacklisted) |

## Me

| Method | Path | Body/Query | Returns |
|---|---|---|---|
| GET | `/me` | — | MemberSelf (adds `email`, `safety_contact_*`, `date_of_birth`) |
| PATCH | `/me` | partial profile | MemberSelf |
| POST | `/me/complete-profile` | `{name, gender, bio, categories, photo_url?}` | `{access, refresh, member}` (onboarding completion) |
| POST | `/me/toggle-available` | — | `{available_now}` |
| POST | `/me/toggle-guardian` | — | `{is_guardian}` (+ notification) |
| GET | `/me/applications` | — | `[Application]` (mine, newest first) |

## Members

| Method | Path | Notes |
|---|---|---|
| GET | `/members` | Roster: guardians + available-now first (emergency hub) |
| GET | `/members/{id}` | Public projection only (no email/DOB/safety contact) |

## Posts (the whole marketplace — one pipeline, six kinds)

`kind` ∈ `regular · emergency · gig · room · team · trip`
`type` ∈ `task · company · offer`
`exchange` ∈ `paid · free · treat · expensesCovered · negotiable · barter`
`gender_preference` ∈ `anyone · femaleOnly · maleOnly`

| Method | Path | Body/Query | Notes |
|---|---|---|---|
| GET | `/posts` | `kind, source(nearby\|city), radius_km, types, exchanges, free=1, gender, category, q, saved=1, mine=1, page_size` | Cursor-paginated `{next, previous, results}`; soonest-first; quarantined hidden |
| POST | `/posts` (alias `/posts/create`) | `{type, kind, title, description, category, scheduled_at, duration_minutes, area, exchange, reward_amount, capacity, gender_preference, meeting_preference, has_checkin, payout_note}` | Moderation screen runs server-side (`403 moderation_blocked`); emergency forces high-risk+check-in+free; trip forces medium+check-in. 201 → Task |
| GET | `/posts/{id}` | — | Task detail (+`lat,lng`) |
| POST | `/posts/{id}/start` | — | creator only; requires `confirmed` |
| POST | `/posts/{id}/complete` | — | creator only; +1 completed_count to helper, karma granted |
| POST | `/posts/{id}/cancel` | — | creator only; applicants notified |
| POST | `/posts/{id}/apply` | `{intro_message}` | Rules enforced: not own post, open, one per member, **gender admission (403 `gender_restricted`)**, capacity (409). Creates the chat room + creator greeting |
| GET | `/posts/{id}/applications` | — | creator only |
| POST | `/posts/{id}/save` | — | toggle → `{saved}` |
| POST | `/posts/{id}/repost` | — | toggle → `{reposted}` |
| POST | `/posts/{id}/rate` | `{stars, note}` | mutual review; updates ratee's trust stats |
| POST | `/applications/{id}/select` | — | creator only; others auto-declined; task → `confirmed` |
| POST | `/applications/{id}/withdraw` | — | applicant only |

## Chat (polling)

| Method | Path | Notes |
|---|---|---|
| GET | `/chat/rooms` | My rooms: `{id, application_id, task_id, task_title, application_status, counterpart{id, public_name, photo_url}, unread_for_me, last_message_at}` |
| GET | `/chat/rooms/{id}/messages?since_seq=N` | Incremental: only messages with `seq > N` |
| POST | `/chat/rooms/{id}/send` | `{body}` → message (participant-only; bumps counterpart unread) |
| POST | `/chat/rooms/{id}/read` | Zeroes my unread counter |

## Auctions

| Method | Path | Notes |
|---|---|---|
| GET | `/auctions?live=1` | newest first; lazy-closes ended auctions |
| GET | `/auctions/{id}` | detail + top-10 bids + `platform_fee_amount`, `total_winner_cost` |
| POST | `/auctions` | `{title, description, category, image_url, base_price, buy_it_now_price?, duration_hours, area}`; moderation applies |
| POST | `/uploads` | multipart `file` — JPEG/PNG/WebP, ≤5 MB; `201 {url}` (absolute URL, use as `image_url`) |
| POST | `/auctions/{id}/bids` | `{amount}` — row-locked; must exceed `current_bid`; seller blocked |
| POST | `/auctions/{id}/buy-now` | first caller wins; race-safe |

## Engagement (karma · perks · play · ideas · radar)

| Method | Path | Notes |
|---|---|---|
| GET | `/karma` | `{balance, entries[≤50]}` — ledger is append-only |
| GET | `/perks` | `+ claimed_by_me` per row |
| POST | `/perks/{id}/claim` | spends karma (402 `karma_insufficient`), one per member; → `{code: "NUVRA-XXXXXX", expires_at}` |
| GET | `/challenges` | `+ played_today` per row |
| POST | `/challenges/{id}/play` | `{score}`; once/day server-enforced; win → full reward, else consolation (+10) |
| GET | `/community/ideas` | upvote-sorted; `+ voted_by_me` |
| POST | `/community/ideas/create` | `{title, details, tag}`; self-vote + idea karma (+15) |
| POST | `/community/ideas/{id}/vote` | toggle → `{voted, upvotes}` |
| GET | `/radar` | `{zones[{zone, free, tasks, tea}], available_now_count, guardian_count, sos[≤10]}` — coarse zones only, no member locations |

## Safety & moderation

| Method | Path | Notes |
|---|---|---|
| POST | `/reports` | `{task_id? / member_id?, reason(spam\|inappropriate\|harassment\|fake\|safety\|other), details}` — **auto-quarantines the post** → `{id, status, quarantined}` |
| POST | `/block/block` | `{member_id}` |
| POST | `/block/unblock` | `{member_id}` |

## Notifications

| Method | Path | Notes |
|---|---|---|
| GET | `/notifications?unread=1` | cursor-paginated |
| GET | `/notifications/unread-count` | `{unread}` — cheap poll target |
| POST | `/notifications/read-all` | — |

---

### Client integration notes

- Base URL compile-time: `--dart-define=NUVRA_API_URL=...`; backend mode: `--dart-define=NUVRA_USE_API=true` (default off → demo/mock mode).
- The Flutter `ApiBackend` keeps the exact `MockBackend` method names (`postTask`, `applyToTask`, `claimPerk`...) — screens are backend-agnostic; both implement `BackendContract` (analyzer-enforced).
- Polling cadence: active chat 3s (`since_seq`), auction detail 5s, feeds on focus + pull-to-refresh, radar 60s, notifications 30s.
- Create mutations return optimistic local Tasks (ids `local-<ms>`) and reconcile from the feed refresh.
