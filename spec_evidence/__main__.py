import argparse
import json
from pathlib import Path
import sys
from .contracts import ContractError, MAX_INPUT_BYTES, load_json, spec_digest
from .evidence import check_results
from .proposals import review_proposal
from .presentation import configured_language, with_presentation


def read_bounded(path):
    with Path(path).open("rb") as stream:
        data = stream.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise ContractError("Input exceeds 2 MiB")
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect contracts, JUnit evidence and structured AI proposals.")
    sub = parser.add_subparsers(dest="command", required=True)
    digest = sub.add_parser("digest");digest.add_argument("--spec", required=True)
    check = sub.add_parser("check");check.add_argument("--spec", required=True);check.add_argument("--junit", required=True)
    review = sub.add_parser("review");review.add_argument("--spec", required=True);review.add_argument("--proposal", required=True)
    for command in (digest, check, review):
        command.add_argument("--config", help="Optional JSON configuration containing language: en or es")
        command.add_argument("--language", choices=["en", "es"], help="Human summary language; overrides configuration")
    args = parser.parse_args(argv)
    language = args.language
    try:
        if args.config:
            preference = configured_language(load_json(read_bounded(args.config)))
            language = args.language or preference
        spec = load_json(read_bounded(args.spec))
        if args.command == "digest":
            result = {"spec_sha256": spec_digest(spec)}
        elif args.command == "check":
            result = check_results(spec, read_bounded(args.junit))
        else:
            result = review_proposal(spec, load_json(read_bounded(args.proposal)))
    except (ContractError, OSError) as error:
        print(json.dumps(with_presentation({"status": "invalid_input", "error": str(error)}, language), ensure_ascii=False))
        return 2
    print(json.dumps(with_presentation(result, language), indent=2, ensure_ascii=False))
    return 1 if result.get("status") in {"failed", "needs_revision"} else 0


if __name__ == "__main__":
    sys.exit(main())
