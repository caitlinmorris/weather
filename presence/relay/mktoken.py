"""Generate a bearer token + hash pair for a relay group member.

    python -m presence.relay.mktoken dan

Prints the TOKEN (give to the person, out-of-band, once) and the HASH
(goes into the relay's RELAY_TOKENS secret). The relay never sees the token
itself; the person never needs the hash.
"""

import hashlib
import secrets
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python -m presence.relay.mktoken <person_id>")
        sys.exit(1)
    person = sys.argv[1]
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode()).hexdigest()
    print(f"TOKEN (for {person}'s .env):   RELAY_TOKEN={token}")
    print(f"HASH  (for RELAY_TOKENS):      \"{person}\": \"{digest}\"")


if __name__ == "__main__":
    main()
