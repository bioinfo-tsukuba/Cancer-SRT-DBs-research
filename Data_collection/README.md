# README

## 1. Overview
This directory contains all resources, scripts, and documentation used to collect, harmonize, and preprocess metadata from 19 publicly available spatial transcriptomics (SRT) databases.

## 2. Database sources
The following 19 SRT databases were included in this collection process.
Each database is cited with its corresponding reference and publication source.
| **Database** | **Citation information** |
|--------------|--------------------------|
| **Aquila** | Zheng Y, Chen Y, Ding X, Wong KH, Cheung E. Aquila: a spatial omics database and analysis platform. Nucleic Acids Res. 2023 Jan 6;51(D1):D827-D834. doi: 10.1093/nar/gkac874. PMID: 36243967; PMCID: PMC9825501. |
| **CROST** | Wang G, Wu S, Xiong Z, Qu H, Fang X, Bao Y. CROST: a comprehensive repository of spatial transcriptomics. Nucleic Acids Res. 2024 Jan 5;52(D1):D882-D890. doi: 10.1093/nar/gkad782. PMID: 37791883; PMCID: PMC10773281. |
| **DeepSpaceDB** | Honcharuk V, Zainab A, Horimoto Y, Takemoto K, Diez D, Kawaoka S, et al.. DeepSpaceDB: a spatial transcriptomics atlas for interactive in-depth analysis of tissues and tissue microenvironments. bioRxiv. doi: 10.1101/2025.01.05.631419 |
| **HCCDB v2.0** | Jiang Z, Wu Y, Miao Y, Deng K, Yang F, Xu S, Wang Y, You R, Zhang L, Fan Y, Guo W, Lian Q, Chen L, Zhang X, Zheng Y, Gu J. HCCDB v2.0: Decompose Expression Variations by Single-cell RNA-seq and Spatial Transcriptomics in HCC. Genomics Proteomics Bioinformatics. 2024 May 9;22(1):qzae011. doi: 10.1093/gpbjnl/qzae011. PMID: 38886186; PMCID: PMC11423853. |
| **HISSTA** | Yu J, Moon J, Kim M, Han G, Jang I, Lim J, Lee S, Yoon SH, Park WY, Lee B, Lee S. HISSTA: a human in situ single-cell transcriptome atlas. Bioinformatics. 2025 Mar 29;41(4):btaf142. doi: 10.1093/bioinformatics/btaf142. PMID: 40163697; PMCID: PMC12002909. |
| **HTAN** | Rozenblatt-Rosen O, Regev A, Oberdoerffer P, Nawy T, Hupalowska A, Rood JE, Ashenberg O, Cerami E, Coffey RJ, Demir E, Ding L, Esplin ED, Ford JM, Goecks J, Ghosh S, Gray JW, Guinney J, Hanlon SE, Hughes SK, Hwang ES, Iacobuzio-Donahue CA, Jané-Valbuena J, Johnson BE, Lau KS, Lively T, Mazzilli SA, Pe'er D, Santagata S, Shalek AK, Schapiro D, Snyder MP, Sorger PK, Spira AE, Srivastava S, Tan K, West RB, Williams EH; Human Tumor Atlas Network. The Human Tumor Atlas Network: Charting Tumor Transitions across Space and Time at Single-Cell Resolution. Cell. 2020 Apr 16;181(2):236-249. doi: 10.1016/j.cell.2020.03.053. PMID: 32302568; PMCID: PMC7376497. |
| **LnCeCell 2.0** | Guo Q, Liu Q, He D, Xin M, Dai Y, Sun R, Li H, Zhang Y, Li J, Kong C, Gao Y, Zhi H, Li F, Ning S, Wang P. LnCeCell 2.0: an updated resource for lncRNA-associated ceRNA networks and web tools based on single-cell and spatial transcriptomics sequencing data. Nucleic Acids Res. 2025 Jan 6;53(D1):D107-D115. doi: 10.1093/nar/gkae947. PMID: 39470723; PMCID: PMC11701739. |
| **Pairpot** | Ruan Z, Lin F, Zhang Z, Cao J, Xiang W, Wei X, Liu J. Pairpot: a database with real-time lasso-based analysis tailored for paired single-cell and spatial transcriptomics. Nucleic Acids Res. 2025 Jan 6;53(D1):D1087-D1098. doi: 10.1093/nar/gkae986. PMID: 39494542; PMCID: PMC11701735. |
| **SCAN** | Deng Y, Lu Y, Li M, Shen J, Qin S, Zhang W, Zhang Q, Shen Z, Li C, Jia T, Chen P, Peng L, Chen Y, Zhang W, Liu H, Zhang L, Rong L, Wang X, Chen D. SCAN: Spatiotemporal Cloud Atlas for Neural cells. Nucleic Acids Res. 2024 Jan 5;52(D1):D998-D1009. doi: 10.1093/nar/gkad895. PMID: 37930842; PMCID: PMC10767991. |
| **SMTdb** | Zhou W, Yang Q, Guo J, Li S, Su M, Leng F, Rong T, Shi J, Gao Y, Jiang T, Xu J, Li Y. SMTdb: A Comprehensive Spatial Meta-Transcriptome Resource in Cancer. Mol Biol Evol. 2025 Oct 29;42(11):msaf263. doi: 10.1093/molbev/msaf263. PMID: 41092484; PMCID: PMC12596269. |
| **SOAR** | Li Y, Ding Y, Dennis S, Hutch MR, Zhou J, Zhou Y, Li Y, Pillai M, Ghotbaldini S, Garcia MA, Broad MS, Mao C, Dulai PS, Cheng F, Zeng Z, Luo Y. SOAR elucidates biological insights and empowers drug discovery through spatial transcriptomics. Sci Adv. 2025 Jun 13;11(24):eadt7450. doi: 10.1126/sciadv.adt7450. Epub 2025 Jun 11. PMID: 40498826. |
| **SODB** | Yuan Z, Pan W, Zhao X, Zhao F, Xu Z, Li X, Zhao Y, Zhang MQ, Yao J. SODB facilitates comprehensive exploration of spatial omics data. Nat Methods. 2023 Mar;20(3):387-399. doi: 10.1038/s41592-023-01773-7. Epub 2023 Feb 16. Erratum in: Nat Methods. 2023 Apr;20(4):623. doi: 10.1038/s41592-023-01844-9. PMID: 36797409. |
| **SORC** | Zhou W, Su M, Jiang T, Yang Q, Sun Q, Xu K, Shi J, Yang C, Ding N, Li Y, Xu J. SORC: an integrated spatial omics resource in cancer. Nucleic Acids Res. 2024 Jan 5;52(D1):D1429-D1437. doi: 10.1093/nar/gkad820. PMID: 37811897; PMCID: PMC10768140. |
| **SPathDB** | Li F, Song X, Fan W, Pei L, Liu J, Zhao R, Zhang Y, Li M, Song K, Sun Y, Zhang C, Zhang Y, Xu Y. SPathDB: a comprehensive database of spatial pathway activity atlas. Nucleic Acids Res. 2025 Jan 6;53(D1):D1205-D1214. doi: 10.1093/nar/gkae1041. PMID: 39546631; PMCID: PMC11701687. |
| **SpatialRef** | Cui T, Li YY, Li BL, Zhang H, Yu TT, Zhang JN, Qian FC, Yin MX, Fang QL, Hu ZH, Yan YX, Wang QY, Li CQ, Shang DS. SpatialRef: a reference of spatial omics with known spot annotation. Nucleic Acids Res. 2025 Jan 6;53(D1):D1215-D1223. doi: 10.1093/nar/gkae892. PMID: 39417483; PMCID: PMC11701618. |
| **SpatialTME** | Shi J, Wei X, Xun Z, Ding X, Liu Y, Liu L, Ye Y. The Web-Based Portal SpatialTME Integrates Histological Images with Single-Cell and Spatial Transcriptomics to Explore the Tumor Microenvironment. Cancer Res. 2024 Apr 15;84(8):1210-1220. doi: 10.1158/0008-5472.CAN-23-2650. PMID: 38315776. |
| **STAr** | Jiang X, Luo D, Fern Ndez E, Yang J, Li H, Jin KW, Zhan Y, Yao B, Bedi S, Xiao G, Zhan X, Li Q, Xie Y. Spatial Transcriptomics Arena (STAr): an Integrated Platform for Spatial Transcriptomics Methodology Research. bioRxiv [Preprint]. 2023 Mar 12:2023.03.10.532127. doi: 10.1101/2023.03.10.532127. PMID: 36945650; PMCID: PMC10028992. |
| **STOmicsDB** | Xu Z, Wang W, Yang T, Li L, Ma X, Chen J, Wang J, Huang Y, Gould J, Lu H, Du W, Sahu SK, Yang F, Li Z, Hu Q, Hua C, Hu S, Liu Y, Cai J, You L, Zhang Y, Li Y, Zeng W, Chen A, Wang B, Liu L, Chen F, Ma K, Xu X, Wei X. STOmicsDB: a comprehensive database for spatial transcriptomics data sharing, analysis and visualization. Nucleic Acids Res. 2024 Jan 5;52(D1):D1053-D1061. doi: 10.1093/nar/gkad933. PMID: 37953328; PMCID: PMC10767841. |
| **stSNV** | Yang C, Liu Y, Wang X, Jia Q, Fan Y, Lu Z, Shi J, Liu Z, Chen G, Li J, Lu W, Zhou W, Lv D, Zou H, Xu J, Li Y, Jiang Q, Wang T, Shao T. stSNV: a comprehensive resource of SNVs in spatial transcriptome. Nucleic Acids Res. 2025 Jan 6;53(D1):D1224-D1234. doi: 10.1093/nar/gkae945. PMID: 39470702; PMCID: PMC11701523. |

## 3. Contents
This project consists of 19 subprojects corresponding to each database.
See each folder and README.md in it for more details.

## 4 Dependency information

#### Python
We used `Python 3.11.8` for this study.

#### Dependency file
The required Python packages for each project are listed in `requirements.txt` in each project folder.
See README in each folder for details.