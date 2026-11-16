"""Copy the current report and one flat-run animation into the ignored delivery.

The project stays in its existing root. The partial submission contains neither
a project clone nor an HTML landing page. Run after the flat study and LaTeX build.
"""

from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def main():
    files=[(ROOT/'report/main.pdf','report.pdf'),
           (ROOT/'results/flat/field_evolution.gif','flat-standing-wave.gif')]
    for source,_ in files:
        if not source.is_file():
            raise FileNotFoundError(f'Run the flat validation and compile the report first: {source}')
    destination=ROOT/'partial-submission'
    destination.mkdir(exist_ok=True)
    for source,name in files:
        shutil.copy2(source,destination/name)
    print('Partial submission: partial-submission/report.pdf and flat-standing-wave.gif')


if __name__=='__main__':
    main()
