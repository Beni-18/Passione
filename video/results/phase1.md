# Passioné v2, phase 1 results

19,738 micro-videos, positive rate 25.0%, test share 20%, seeds [0, 1, 2, 3, 4].

## Is the label mostly about age?

Age alone predicts the raw label at ROC-AUC 0.542. The raw and age-adjusted labels agree on 97.7% of videos.

| age fifth | trending rate | median age (days) | median views |
|:--|--:|--:|--:|
| newest | 19.4% | 15 | 730,500 |
| 2nd | 24.9% | 34 | 953,000 |
| 3rd | 27.2% | 58 | 1,082,623 |
| 4th | 26.2% | 81 | 1,046,777 |
| oldest | 27.4% | 134 | 1,089,000 |

## ROC-AUC, raw label (mean ± std over seeds)

| features | linear | boosting | fusion |
|:--|--:|--:|--:|
| title words | 0.640 ± 0.006 | 0.608 ± 0.003 | 0.622 ± 0.010 |
| + title meaning | 0.650 ± 0.006 | 0.638 ± 0.005 | 0.642 ± 0.008 |
| + cover image | 0.704 ± 0.007 | 0.693 ± 0.006 | 0.701 ± 0.006 |
| + video content | 0.704 ± 0.007 | 0.694 ± 0.007 | 0.702 ± 0.009 |
| cover only | 0.698 ± 0.008 | 0.684 ± 0.008 | 0.698 ± 0.007 |
| video only | 0.592 ± 0.009 | 0.576 ± 0.008 | 0.593 ± 0.011 |

## ROC-AUC, age-adjusted label (mean ± std over seeds)

| features | linear | boosting | fusion |
|:--|--:|--:|--:|
| title words | 0.639 ± 0.005 | 0.606 ± 0.008 | 0.626 ± 0.004 |
| + title meaning | 0.651 ± 0.007 | 0.633 ± 0.012 | 0.647 ± 0.006 |
| + cover image | 0.700 ± 0.005 | 0.689 ± 0.007 | 0.699 ± 0.004 |
| + video content | 0.699 ± 0.006 | 0.688 ± 0.007 | 0.696 ± 0.005 |

## Paired comparisons (ROC-AUC gain, 95% paired bootstrap)

| label | model | question | gain | 95% interval | real? |
|:--|:--|:--|--:|:--|:--|
| raw | linear | title meaning (BGE-M3) on top of title words | +0.009 | [+0.004, +0.015] | yes |
| raw | linear | cover image (CLIP) on top of the title | +0.054 | [+0.048, +0.060] | yes |
| raw | linear | video content (VideoMAE) on top of title and cover | +0.000 | [-0.001, +0.002] | no |
| raw | boosting | title meaning (BGE-M3) on top of title words | +0.030 | [+0.023, +0.037] | yes |
| raw | boosting | cover image (CLIP) on top of the title | +0.056 | [+0.049, +0.063] | yes |
| raw | boosting | video content (VideoMAE) on top of title and cover | +0.000 | [-0.002, +0.002] | no |
| raw | fusion | title meaning (BGE-M3) on top of title words | +0.020 | [+0.012, +0.028] | yes |
| raw | fusion | cover image (CLIP) on top of the title | +0.059 | [+0.052, +0.065] | yes |
| raw | fusion | video content (VideoMAE) on top of title and cover | +0.002 | [-0.001, +0.004] | no |
| raw | boosting vs linear | non-linear fusion, all inputs | -0.010 | [-0.015, -0.006] | yes |
| raw | fusion vs linear | non-linear fusion, all inputs | -0.002 | [-0.005, +0.001] | no |
| age_adjusted | linear | title meaning (BGE-M3) on top of title words | +0.012 | [+0.007, +0.018] | yes |
| age_adjusted | linear | cover image (CLIP) on top of the title | +0.049 | [+0.043, +0.055] | yes |
| age_adjusted | linear | video content (VideoMAE) on top of title and cover | -0.001 | [-0.003, +0.001] | no |
| age_adjusted | boosting | title meaning (BGE-M3) on top of title words | +0.027 | [+0.020, +0.034] | yes |
| age_adjusted | boosting | cover image (CLIP) on top of the title | +0.056 | [+0.049, +0.063] | yes |
| age_adjusted | boosting | video content (VideoMAE) on top of title and cover | -0.001 | [-0.003, +0.001] | no |
| age_adjusted | fusion | title meaning (BGE-M3) on top of title words | +0.021 | [+0.014, +0.028] | yes |
| age_adjusted | fusion | cover image (CLIP) on top of the title | +0.052 | [+0.046, +0.058] | yes |
| age_adjusted | fusion | video content (VideoMAE) on top of title and cover | -0.003 | [-0.006, -0.000] | yes |
| age_adjusted | boosting vs linear | non-linear fusion, all inputs | -0.012 | [-0.016, -0.007] | yes |
| age_adjusted | fusion vs linear | non-linear fusion, all inputs | -0.003 | [-0.006, -0.000] | yes |

## Ranking, without a cut-off

Spearman correlation between the model's score and log views, over 13,236 test videos (each counted once): 0.425.

## Calibration (linear, + video content)

| scores | ECE | Brier | mean score |
|:--|--:|--:|--:|
| as trained | 0.211 | 0.215 | 0.461 |
| isotonic (cross-fit) | 0.009 | 0.170 | 0.250 |
| base rate | | | 0.250 |

## Where it goes wrong

Cut-off for trending: 2,148,000 views. "Near the cut-off" means within a factor of 1.4 either side.

**age fifth**

| slice | n | ROC-AUC | accuracy at 0.5 | trending rate |
|:--|--:|--:|--:|--:|
| newest | 2,648 | 0.705 | 66.5% | 19.6% |
| 2nd | 2,647 | 0.719 | 65.2% | 24.0% |
| 3rd | 2,647 | 0.717 | 65.4% | 26.6% |
| 4th | 2,647 | 0.723 | 67.1% | 26.9% |
| oldest | 2,647 | 0.664 | 64.1% | 28.4% |

**title length**

| slice | n | ROC-AUC | accuracy at 0.5 | trending rate |
|:--|--:|--:|--:|--:|
| 0-3 words | 982 | 0.691 | 64.5% | 22.3% |
| 4-7 | 3,248 | 0.700 | 62.6% | 27.6% |
| 8-12 | 3,495 | 0.706 | 64.9% | 25.7% |
| 13+ | 5,511 | 0.708 | 68.1% | 23.7% |

**views vs cut-off**

| slice | n | ROC-AUC | accuracy at 0.5 | trending rate |
|:--|--:|--:|--:|--:|
| far below | 4,903 | n/a | 78.0% | 0.0% |
| below | 3,648 | n/a | 59.1% | 0.0% |
| near the cut-off | 2,465 | 0.520 | 49.8% | 44.7% |
| above | 1,575 | n/a | 62.9% | 100.0% |
| far above | 645 | n/a | 76.6% | 100.0% |

**Most confident mistakes** (score averaged over the seeds where the video was in the test set)

| type | score | views | title |
|:--|--:|--:|:--|
| false positive | 0.90 | 2,111,573 | the security bully elementary school students did not think that the s |
| false positive | 0.89 | 1,184,097 | # The movie six doors of the blood bug mystery case in the film and te |
| false positive | 0.89 | 1,065,808 | the people according to the amount of food |
| false positive | 0.88 | 859,000 | # movie dragon gave birth to nine children # I am in fast hands to cat |
| false positive | 0.87 | 1,377,078 | the wife under the critically ill notice |
| false negative | 0.06 | 4,135,000 | (My Three Brothers) Episode 1 to be continued. #ooc apologies # Not or |
| false negative | 0.09 | 3,180,907 | male: Shen Brother no! # Comics recommendation # Comics commentary # c |
| false negative | 0.13 | 2,426,000 | # real events real events (when military training last year) was reall |
| false negative | 0.13 | 3,004,000 | September play Shuai secret: flash # orange right Jing new skin |
| false negative | 0.14 | 2,378,000 | episode 21 / about my fan is a pervert |
