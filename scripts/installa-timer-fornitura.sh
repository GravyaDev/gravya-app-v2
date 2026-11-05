#!/usr/bin/env bash
# Installa (o aggiorna) il timer systemd utente dei controlli settimanali della
# catena di fornitura. Idempotente: puo' essere rieseguito; riscrive le unita'
# con il percorso del repository e riabilita il timer.
#
# Uso: scripts/installa-timer-fornitura.sh [--destinazione DIR] [--senza-systemctl] [--anche-da-worktree]
#   --destinazione DIR     dove scrivere le unita' (default: ~/.config/systemd/user)
#   --senza-systemctl      scrive soltanto i file (per verifica e prove)
#   --anche-da-worktree    consente di partire da un worktree (di norma si rifiuta:
#                          il worktree viene cancellato dopo il merge e il timer
#                          punterebbe a un percorso che non esiste piu')
set -euo pipefail

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RADICE="$(cd "$QUI/.." && pwd)"
DESTINAZIONE="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SYSTEMCTL=1
DA_WORKTREE=0
UNITA=(gravya-fornitura.service gravya-fornitura.timer)

while [ $# -gt 0 ]; do
  case "$1" in
    --destinazione) DESTINAZIONE="${2:?manca la cartella}"; shift 2 ;;
    --senza-systemctl) SYSTEMCTL=0; shift ;;
    --anche-da-worktree) DA_WORKTREE=1; shift ;;
    *) echo "Opzione sconosciuta: $1" >&2; exit 2 ;;
  esac
done

if [ "$DA_WORKTREE" -eq 0 ] && [ "$(git -C "$RADICE" rev-parse --git-dir)" != "$(git -C "$RADICE" rev-parse --git-common-dir)" ]; then
  echo "ERRORE: $RADICE e' un worktree, non il repository principale. Esegui lo script dal repository principale." >&2
  exit 2
fi
case "$RADICE" in
  *[[:space:]\&\|\\]*) echo "ERRORE: il percorso del repository contiene spazi o caratteri speciali: $RADICE" >&2; exit 2 ;;
esac

mkdir -p "$DESTINAZIONE"
for u in "${UNITA[@]}"; do
  sed "s|@RADICE@|$RADICE|g" "$RADICE/systemd/$u" > "$DESTINAZIONE/$u.nuovo"
  mv -f "$DESTINAZIONE/$u.nuovo" "$DESTINAZIONE/$u"
  echo "scritta: $DESTINAZIONE/$u"
done

if [ "$SYSTEMCTL" -eq 1 ]; then
  systemctl --user daemon-reload
  systemctl --user enable --now gravya-fornitura.timer
  systemctl --user list-timers gravya-fornitura.timer --no-pager
fi
