"""Run the Part 3 examples together and save their output."""

import io
import contextlib

import advisory_agent
import extract_disclosure
import debate
import dcf_calculator


def capture(label, fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        print(f"\n{'#' * 60}\n{label}\n{'#' * 60}\n")
        fn()
    return buf.getvalue()


def main():
    sections = [
        ("Part A - Portfolio advisory", advisory_agent.main),
        ("Part B - Disclosure extraction", extract_disclosure.main),
        ("Part C - Bull / bear debate", debate.run_debate),
        ("Part D - DCF valuation", dcf_calculator.main),
    ]

    full_transcript = []
    for label, fn in sections:
        full_transcript.append(capture(label, fn))

    transcript_text = "\n".join(full_transcript)
    with open("run_transcript.txt", "w") as f:
        f.write(transcript_text)

    print(transcript_text)
    print("\n\nWrote run_transcript.txt")


if __name__ == "__main__":
    main()
