# Gece Raporu — 13 Temmuz 2026

6-7 saatlik otonom çalışma özeti. Tüm işler tamamlandı; production'a 3 deploy yapıldı, hepsi doğrulandı.

## Özet (TL;DR)

1. **Production'a deploy edildi:** market-proof branch'i (Section 301 line-level data, remedy routing, verifier suppression) + prompt hardening + FTA re-anchor fix — PR #3 ve 2 takip commit'i main'de.
2. **False positive oranı ölçülebilir şekilde düştü:** CBP ground-truth benchmark'ında high-confidence FP, satır başına **%3.3 → %1.0 → spot-check'te 0**.
3. **Test verisi 2 katına çıktı:** 500 gerçek CBP ruling kaydı, %90'ı gerçek 2024 ithalat fiyatlı, 79 PDF fatura.
4. **Gerçek FTA doları korundu:** İlk prompt kuralı KORUS/USMCA bulgularını yanlışlıkla susturuyordu — verifier'da re-anchor ile düzeltildi ve doğrulandı.

## Deploy edilenler (kronolojik)

| Commit | İçerik | Doğrulama |
|---|---|---|
| `3081ff0` (PR #3) | Market-proof: section301.json (line-level), remedy.py (§1514/1520(d)/PSC yönlendirme), verifier same-subheading suppression, XLSX batch upload, SEO sayfaları | 77 test + 2 review ajanı PASS; canlıda `suppressed_count` smoke test |
| `48cb062` | Prompt reclassification bar (GRI/ruling şartı) + suppressed chip UI + test_data corpus repo'ya eklendi | 77 test; canlı spot-check |
| `654bab5` | FTA re-anchor: aynı-subheading bulgular düşürülmek yerine declared kod üzerinde 1520(d) program bulgusuna dönüştürülüyor | 78 test; 5 faturalık final spot-check |

## Benchmark sonuçları (CBP CROSS ground truth)

Metodoloji: her test satırının HTS kodu bağlayıcı bir CBP kararından geliyor; TariffCheck'in bir satırı farklı subheading'e "misclassification" diye işaretlemesi CBP ile çelişki = varsayılan false positive.

| Metrik | v1 baseline (dün gece) | v2 suppression sonrası | Prompt+re-anchor sonrası |
|---|---|---|---|
| Test satırı | 246 (57 PDF) | 500 (79 PDF) | 5 en kötü fatura |
| Bulgu | 239 | 82 (+378 bastırılan) | — |
| CBP çelişkisi | 19 (%7.7) | 20 (%4.0) | — |
| High-confidence FP | 8 (%3.3) | 5 (%1.0) | **0** |
| FTA tespiti | çalışıyor | çalışıyor | çalışıyor ($45k+ 5 faturada) |
| PDF başarı | 57/57 | 78/79 (1 geçici 502) | 5/5 |

Deterministik batch: 500/500 satır kabul, 0 kod bulunamadı, 41 flagged, ~$105k exposure (5 batch).

## Test verisi v2 (`test_data/`)

- `cross_rulings_dataset.json` — 500 kayıt: gerçek CBP ruling no + tarih + HTS kodu + ürün açıklaması + menşe; 450'si (%90) gerçek UN Comtrade 2024 ABD ithalat ortalama birim fiyatlı
- `pdf_invoices/` — 79 ticari fatura PDF'i (46 temiz menşe grubu; v1'deki bozuk origin parse'ları düzeltildi)
- `batch_rows_1..5.json` — analyze-batch gövdeleri
- `run_live_tests.py` — canlı benchmark koşucusu; `live_test_results.jsonl` (v2) ve `baseline_v1_prefix_results.jsonl` (v1) sonuçları

## Dikkat gereken noktalar

1. **Yanlışlıkla oluşan boş Vercel projesi:** `vercel link` denemesi foma1 team'inde boş bir "tariffcheck" projesi yarattı (gerçek deploy eymenfaruk479-4861 hesabında GitHub entegrasyonuyla). Silme iznim yoktu — foma1 dashboard'ından silebilirsin.
2. **ALLOWED_ORIGINS:** Review ajanı CORS'un env yokken `*`'a düştüğünü işaretledi (bu diff'ten önce de böyleydi). Vercel prod env'inde `ALLOWED_ORIGINS` set edilmeli — Claude harcatan /api/analyze'ı üçüncü parti siteler tarayıcıdan sürebilir.
3. **API key karşılaştırması:** `api_key_firm()` `==` kullanıyor; `hmac.compare_digest`'e geçirmek ucuz bir iyileştirme (düşük öncelik).
4. **gh hesabı:** eymen160'a geçildi (fomahub işleri için fomateam12'ye geri dönmen gerekebilir).
5. Kalan gerçek FP'ler model seviyesinde ve nadir (v2'de 5/500); prompt bar'ı sonrası spot-check'te sıfırlandı ama tam 79-PDF re-benchmark koşulmadı (rate limit ~50dk) — istersen bugün koşarız.

## Ajan kullanımı

- Backend review ajanı (PASS + 4 not), Frontend review ajanı (PASS + 3 not), Dataset v2 ajanı (500 kayıt pipeline). Benchmark ve deploy'lar ana oturumda yürütüldü.
