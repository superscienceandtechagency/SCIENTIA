"""Fixed synthetic passages and independent judgments for benchmark v2."""

from dataclasses import dataclass
from uuid import UUID

from scientia.evidence import Passage

BENCHMARK_ID = "synthetic-lexical-v2"

SOURCE_TRIAL = UUID("10000000-0000-0000-0000-000000000001")
SOURCE_COHORT = UUID("10000000-0000-0000-0000-000000000002")
SOURCE_GREENHOUSE = UUID("10000000-0000-0000-0000-000000000003")
SOURCE_WIND_TUNNEL = UUID("10000000-0000-0000-0000-000000000004")
SOURCE_ASTRONOMY = UUID("10000000-0000-0000-0000-000000000005")
SOURCE_ASSAY = UUID("10000000-0000-0000-0000-000000000006")
SOURCE_CELLULAR = UUID("10000000-0000-0000-0000-000000000007")

PASSAGE_FEVER_TRIAL = UUID("20000000-0000-0000-0000-000000000001")
PASSAGE_COHORT_EVENTS = UUID("20000000-0000-0000-0000-000000000002")
PASSAGE_TRIAL_EVENTS = UUID("20000000-0000-0000-0000-000000000003")
PASSAGE_IRRIGATION = UUID("20000000-0000-0000-0000-000000000004")
PASSAGE_TURBINE = UUID("20000000-0000-0000-0000-000000000005")
PASSAGE_GREENHOUSE_CONTROL = UUID("20000000-0000-0000-0000-000000000006")
PASSAGE_EXACT_ASSAY = UUID("20000000-0000-0000-0000-000000000007")
PASSAGE_CELLULAR_RELEVANT = UUID("20000000-0000-0000-0000-000000000008")
PASSAGE_CELLULAR_DECOY = UUID("20000000-0000-0000-0000-000000000009")
PASSAGE_GLYCOLYSIS = UUID("20000000-0000-0000-0000-000000000010")

SYNTHETIC_PASSAGES = (
    Passage(
        passage_id=PASSAGE_FEVER_TRIAL,
        source_id=SOURCE_TRIAL,
        text=(
            "Synthetic randomized trial: compound A reduced fever incidence "
            "at eight weeks."
        ),
    ),
    Passage(
        passage_id=PASSAGE_COHORT_EVENTS,
        source_id=SOURCE_COHORT,
        text=(
            "Synthetic study recorded and reported adverse events for "
            "compound B."
        ),
    ),
    Passage(
        passage_id=PASSAGE_TRIAL_EVENTS,
        source_id=SOURCE_TRIAL,
        text=(
            "Synthetic randomized trial reported adverse events for "
            "compound B."
        ),
    ),
    Passage(
        passage_id=PASSAGE_IRRIGATION,
        source_id=SOURCE_GREENHOUSE,
        text=(
            "Synthetic greenhouse experiment found saline irrigation reduce "
            "soil salinity in seedlings."
        ),
    ),
    Passage(
        passage_id=PASSAGE_TURBINE,
        source_id=SOURCE_WIND_TUNNEL,
        text=(
            "Synthetic wind tunnel study measured turbine blade vibration "
            "at high airflow."
        ),
    ),
    Passage(
        passage_id=PASSAGE_GREENHOUSE_CONTROL,
        source_id=SOURCE_GREENHOUSE,
        text=(
            "Synthetic greenhouse trial compared a model of irrigation "
            "impacts on seedlings."
        ),
    ),
    Passage(
        passage_id=PASSAGE_EXACT_ASSAY,
        source_id=SOURCE_ASSAY,
        text=(
            "Synthetic assay reports enzyme X activation after compound A "
            "exposure."
        ),
    ),
    Passage(
        passage_id=PASSAGE_CELLULAR_RELEVANT,
        source_id=SOURCE_CELLULAR,
        text=(
            "Mitochondrial phosphorylation produces ATP from carbohydrate."
        ),
    ),
    Passage(
        passage_id=PASSAGE_CELLULAR_DECOY,
        source_id=SOURCE_ASSAY,
        text=(
            "A synthetic cellular energy glucose ATP phrase repeats cellular "
            "energy glucose ATP."
        ),
    ),
    Passage(
        passage_id=PASSAGE_GLYCOLYSIS,
        source_id=SOURCE_CELLULAR,
        text=(
            "Adenosine triphosphate supplies the cell's usable fuel."
        ),
    ),
)


@dataclass(frozen=True)
class SyntheticJudgment:
    query_id: str
    query: str
    relevant_passage_ids: frozenset[UUID]
    rationale: str


SYNTHETIC_JUDGMENTS = (
    SyntheticJudgment(
        query_id="fever-trial",
        query="Which synthetic randomized trial reduced fever incidence?",
        relevant_passage_ids=frozenset({PASSAGE_FEVER_TRIAL}),
        rationale=(
            "The constructed passage explicitly states that compound A reduced "
            "fever incidence in a synthetic randomized trial."
        ),
    ),
    SyntheticJudgment(
        query_id="compound-adverse-events",
        query="Which synthetic study reported adverse events for compound B?",
        relevant_passage_ids=frozenset(
            {PASSAGE_COHORT_EVENTS, PASSAGE_TRIAL_EVENTS}
        ),
        rationale=(
            "Both constructed passages explicitly report adverse events for "
            "compound B; other passages do not."
        ),
    ),
    SyntheticJudgment(
        query_id="saline-irrigation",
        query="What did saline irrigation reduce in greenhouse seedlings?",
        relevant_passage_ids=frozenset({PASSAGE_IRRIGATION}),
        rationale=(
            "The synthetic greenhouse passage explicitly says saline "
            "irrigation reduced soil salinity in seedlings."
        ),
    ),
    SyntheticJudgment(
        query_id="astronomy-unknown",
        query="What did the synthetic astronomy model measure?",
        relevant_passage_ids=frozenset(),
        rationale=(
            "This intentionally unjudged query has no astronomy passage in the "
            "synthetic corpus; lexical matches are not relevance labels."
        ),
    ),
    SyntheticJudgment(
        query_id="exact-assay-match",
        query="Synthetic assay reports enzyme X activation after compound A exposure",
        relevant_passage_ids=frozenset({PASSAGE_EXACT_ASSAY}),
        rationale=(
            "The exact constructed phrase is in the assay passage, which "
            "describes enzyme X activation after compound A exposure."
        ),
    ),
    SyntheticJudgment(
        query_id="partial-saline-match",
        query="saline seedlings",
        relevant_passage_ids=frozenset({PASSAGE_IRRIGATION}),
        rationale=(
            "The label is based on the constructed passage's explicit saline "
            "irrigation and seedling result; another passage mentioning "
            "seedlings and irrigation is a deliberate partial lexical distractor."
        ),
    ),
    SyntheticJudgment(
        query_id="cellular-energy-rank-error",
        query="cellular energy glucose ATP",
        relevant_passage_ids=frozenset({PASSAGE_CELLULAR_RELEVANT}),
        rationale=(
            "The synthetic mitochondrial passage links carbohydrate to ATP; "
            "the passage repeating query terms is a deliberately irrelevant "
            "textual decoy."
        ),
    ),
    SyntheticJudgment(
        query_id="missing-lexical-terms",
        query="Which molecule fuels biological work?",
        relevant_passage_ids=frozenset({PASSAGE_GLYCOLYSIS}),
        rationale=(
            "The constructed passage names adenosine triphosphate as cellular "
            "fuel; the query uses different terms, intentionally testing "
            "lexical synonym failure."
        ),
    ),
)
