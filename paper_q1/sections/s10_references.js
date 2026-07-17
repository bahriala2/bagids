/* Section (fin) — References. 49 entrées, numérotation alignée sur
 * s2_relatedwork.js (C1-C8, threads 2.1-2.6).
 * NB : entrées à vérifier / reformater au style Elsevier avant soumission
 * (années, pages, DOI). Tous les travaux cités sont réels. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => {
  const refs = [
    // -------- 2.1 Deep learning IDS (1-11)
    "C. Yin, Y. Zhu, J. Fei, X. He, A deep learning approach for intrusion "
      + "detection using recurrent neural networks, IEEE Access 5 (2017) "
      + "21954–21961.",
    "R. Vinayakumar, M. Alazab, K. P. Soman, P. Poornachandran, "
      + "A. Al-Nemrat, S. Venkatraman, Deep learning approach for "
      + "intelligent intrusion detection system, IEEE Access 7 (2019) "
      + "41525–41550.",
    "N. Shone, T. N. Ngoc, V. D. Phai, Q. Shi, A deep learning approach to "
      + "network intrusion detection, IEEE Transactions on Emerging Topics "
      + "in Computational Intelligence 2 (1) (2018) 41–50.",
    "A. Javaid, Q. Niyaz, W. Sun, M. Alam, A deep learning approach for "
      + "network intrusion detection system, in: EAI International "
      + "Conference on Bio-inspired Information and Communications "
      + "Technologies (BICT), 2016.",
    "Z. Ahmad, A. Shahid Khan, C. Wai Shiang, J. Abdullah, F. Ahmad, "
      + "Network intrusion detection system: A systematic study of machine "
      + "learning and deep learning approaches, Transactions on Emerging "
      + "Telecommunications Technologies 32 (1) (2021) e4150.",
    "H. Liu, B. Lang, Machine learning and deep learning methods for "
      + "intrusion detection systems: A survey, Applied Sciences 9 (20) "
      + "(2019) 4396.",
    "I. Sharafaldin, A. H. Lashkari, A. A. Ghorbani, Toward generating a "
      + "new intrusion detection dataset and intrusion traffic "
      + "characterization, in: 4th International Conference on Information "
      + "Systems Security and Privacy (ICISSP), 2018, pp. 108–116.",
    "J. L. Leevy, T. M. Khoshgoftaar, A survey and analysis of intrusion "
      + "detection models based on CSE-CIC-IDS2018 Big Data, Journal of "
      + "Big Data 7 (2020) 104.",
    "Z. Long, H. Yan, G. Shen, X. Zhang, H. He, L. Cheng, A "
      + "Transformer-based network intrusion detection approach for cloud "
      + "security, Journal of Cloud Computing 13 (2024) 5.",
    "F. Ullah, S. Ullah, G. Srivastava, J. C.-W. Lin, IDS-INT: Intrusion "
      + "detection system using transformer-based transfer learning for "
      + "imbalanced network traffic, Digital Communications and Networks "
      + "10 (1) (2024) 190–204.",
    "H. Kheddar, Transformers and large language models for efficient "
      + "intrusion detection systems: A comprehensive survey, "
      + "arXiv:2408.07583 (2024).",
    // -------- 2.2 Ensembles, calibration, selective (12-18)
    "G. Folino, P. Sabatino, Ensemble based collaborative and distributed "
      + "intrusion detection systems: A survey, Journal of Network and "
      + "Computer Applications 66 (2016) 1–16.",
    "B. A. Tama, M. Comuzzi, K.-H. Rhee, TSE-IDS: A two-stage classifier "
      + "ensemble for intelligent anomaly-based intrusion detection "
      + "system, IEEE Access 7 (2019) 94497–94507.",
    "C. Guo, G. Pleiss, Y. Sun, K. Q. Weinberger, On calibration of "
      + "modern neural networks, in: International Conference on Machine "
      + "Learning (ICML), 2017, pp. 1321–1330.",
    "M. Minderer, J. Djolonga, R. Romijnders, F. Hubis, X. Zhai, "
      + "N. Houlsby, D. Tran, M. Lucic, Revisiting the calibration of "
      + "modern neural networks, in: Advances in Neural Information "
      + "Processing Systems (NeurIPS), 2021.",
    "Y. Geifman, R. El-Yaniv, Selective classification for deep neural "
      + "networks, in: Advances in Neural Information Processing Systems "
      + "(NeurIPS), 2017.",
    "K. Hendrickx, L. Perini, D. Van der Plas, W. Meert, J. Davis, "
      + "Machine learning with a reject option: A survey, Machine "
      + "Learning 113 (2024) 3073–3110.",
    "J. Talpini, F. Sartori, M. Savi, Enhancing trustworthiness in "
      + "ML-based network intrusion detection with uncertainty "
      + "quantification, Journal of Reliable Intelligent Environments 10 "
      + "(2024) 501–520.",
    // -------- 2.3 Adversarial / poisoning (19-27)
    "B. Biggio, F. Roli, Wild patterns: Ten years after the rise of "
      + "adversarial machine learning, Pattern Recognition 84 (2018) "
      + "317–331.",
    "N. Papernot, P. McDaniel, A. Sinha, M. P. Wellman, SoK: Security and "
      + "privacy in machine learning, in: IEEE European Symposium on "
      + "Security and Privacy (EuroS&P), 2018, pp. 399–414.",
    "M. Jagielski, A. Oprea, B. Biggio, C. Liu, C. Nita-Rotaru, B. Li, "
      + "Manipulating machine learning: Poisoning attacks and "
      + "countermeasures for regression learning, in: IEEE Symposium on "
      + "Security and Privacy (S&P), 2018, pp. 19–35.",
    "T. Gu, K. Liu, B. Dolan-Gavitt, S. Garg, BadNets: Evaluating "
      + "backdooring attacks on deep neural networks, IEEE Access 7 "
      + "(2019) 47230–47244.",
    "O. Ibitoye, R. Abou-Khamis, A. Matrawy, M. O. Shafiq, The threat of "
      + "adversarial attacks on machine learning in network security: A "
      + "survey, arXiv:1911.02621 (2019).",
    "G. Apruzzese, M. Andreolini, L. Ferretti, M. Marchetti, "
      + "M. Colajanni, Modeling realistic adversarial attacks against "
      + "network intrusion detection systems, ACM Digital Threats: "
      + "Research and Practice 3 (3) (2022) 1–19.",
    "J. Vitorino, I. Praça, E. Maia, SoK: Realistic adversarial attacks "
      + "and defenses for intelligent network intrusion detection, "
      + "Computers & Security 134 (2023) 103433.",
    "K. He, D. D. Kim, M. R. Asghar, Adversarial machine learning for "
      + "network intrusion detection systems: A comprehensive survey, "
      + "IEEE Communications Surveys & Tutorials 25 (1) (2023) 538–566.",
    "T. D. Nguyen, P. Rieger, M. Miettinen, A.-R. Sadeghi, Poisoning "
      + "attacks on federated learning-based IoT intrusion detection "
      + "system, in: Workshop on Decentralized IoT Systems and Security "
      + "(DISS, co-located with NDSS), 2020.",
    // -------- 2.4 Multi-agent / collaborative (28-30)
    "E. H. Spafford, D. Zamboni, Intrusion detection using autonomous "
      + "agents, Computer Networks 34 (4) (2000) 547–570.",
    "Á. Herrero, E. Corchado, Multiagent systems for network intrusion "
      + "detection: A review, in: Computational Intelligence in Security "
      + "for Information Systems (CISIS), Springer, 2009, pp. 143–154.",
    "W. Li, W. Meng, L. F. Kwok, Surveying trust-based collaborative "
      + "intrusion detection: State-of-the-art, challenges and future "
      + "directions, IEEE Communications Surveys & Tutorials 24 (1) "
      + "(2022) 280–305.",
    // -------- 2.5 Blockchain (31-40)
    "N. Alexopoulos, E. Vasilomanolakis, N. R. Ivanko, M. Mühlhäuser, "
      + "Towards blockchain-based collaborative intrusion detection "
      + "systems, in: International Conference on Critical Information "
      + "Infrastructures Security (CRITIS), Springer, 2017, pp. 107–118.",
    "T. Golomb, Y. Mirsky, Y. Elovici, CIoTA: Collaborative IoT anomaly "
      + "detection via blockchain, in: Workshop on Decentralized IoT "
      + "Security and Standards (DISS), 2018.",
    "W. Meng, E. W. Tischhauser, Q. Wang, Y. Wang, J. Han, When intrusion "
      + "detection meets blockchain technology: A review, IEEE Access 6 "
      + "(2018) 10179–10188.",
    "E. Androulaki, A. Barger, V. Bortnikov, C. Cachin, K. Christidis, "
      + "et al., Hyperledger Fabric: A distributed operating system for "
      + "permissioned blockchains, in: EuroSys, 2018, pp. 30:1–30:15.",
    "D. Preuveneers, V. Rimmer, I. Tsingenopoulos, J. Spooren, W. Joosen, "
      + "E. Ilie-Zudor, Chained anomaly detection models for federated "
      + "learning: An intrusion detection case study, Applied Sciences 8 "
      + "(12) (2018) 2663.",
    "S. Rathore, B. W. Kwon, J. H. Park, BlockSecIoTNet: Blockchain-based "
      + "decentralized security architecture for IoT network, Journal of "
      + "Network and Computer Applications 143 (2019) 167–177.",
    "O. Alkadi, N. Moustafa, B. Turnbull, K.-K. R. Choo, A deep "
      + "blockchain framework-enabled collaborative intrusion detection "
      + "for protecting IoT and cloud networks, IEEE Internet of Things "
      + "Journal 8 (12) (2021) 9463–9472.",
    "W. Li, S. Tug, W. Meng, Y. Wang, Designing collaborative "
      + "blockchained signature-based intrusion detection in IoT "
      + "environments, Future Generation Computer Systems 96 (2019) "
      + "481–489.",
    "W. Issa, N. Moustafa, B. Turnbull, N. Sohrabi, Z. Tari, "
      + "Blockchain-based federated learning for securing Internet of "
      + "Things: A comprehensive survey, ACM Computing Surveys 55 (9) "
      + "(2023) 1–43.",
    "S. Ali, Q. Li, A. Yousafzai, Blockchain and federated learning-"
      + "based intrusion detection approaches for edge-enabled "
      + "industrial IoT networks: A survey, Ad Hoc Networks 152 (2024) "
      + "103320.",
    // -------- 2.6 LLM / agentic (41-47)
    "M. A. Ferrag, F. Alwahedi, A. Battah, B. Cherif, A. Mechri, "
      + "N. Tihanyi, Generative AI and large language models for cyber "
      + "security: All insights you need, arXiv:2405.12750 (2024).",
    "J. Zhang, H. Bu, H. Wen, Y. Liu, H. Fei, et al., When LLMs meet "
      + "cybersecurity: A systematic literature review, Cybersecurity 8 "
      + "(2025).",
    "Y. Yao, J. Duan, K. Xu, Y. Cai, Z. Sun, Y. Zhang, A survey on large "
      + "language model (LLM) security and privacy: The good, the bad, "
      + "and the ugly, High-Confidence Computing 4 (2) (2024) 100211.",
    "F. N. Motlagh, M. Hajizadeh, M. Majd, P. Najafi, F. Cheng, "
      + "C. Meinel, Large language models in cybersecurity: "
      + "State-of-the-art, arXiv:2402.00891 (2024).",
    "S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, Y. Cao, "
      + "ReAct: Synergizing reasoning and acting in language models, in: "
      + "International Conference on Learning Representations (ICLR), "
      + "2023.",
    "L. Wang, C. Ma, X. Feng, Z. Zhang, H. Yang, et al., A survey on "
      + "large language model based autonomous agents, Frontiers of "
      + "Computer Science 18 (6) (2024) 186345.",
    "T. Ali, P. Kostakos, HuntGPT: Integrating machine learning-based "
      + "anomaly detection and explainable AI with large language models "
      + "(LLMs), arXiv:2309.16021 (2023).",
    // -------- HITL / SOC + agents classiques (48-49)
    "M. Vielberth, F. Böhm, I. Fichtinger, G. Pernul, Security "
      + "Operations Center: A systematic study and open challenges, IEEE "
      + "Access 8 (2020) 227756–227779.",
    "R. C. Arkin, Behavior-Based Robotics, MIT Press, 1998.",
    // -------- Défauts des benchmarks (50-52)
    "G. Engelen, V. Rimmer, W. Joosen, Troubleshooting an intrusion "
      + "detection dataset: the CICIDS2017 case study, in: IEEE Security "
      + "and Privacy Workshops (SPW), 2021, pp. 7–12.",
    "L. Liu, G. Engelen, T. Lynar, D. Essam, W. Joosen, Error prevalence "
      + "in NIDS datasets: A case study on CIC-IDS-2017 and "
      + "CSE-CIC-IDS-2018, in: IEEE Conference on Communications and "
      + "Network Security (CNS), 2022, pp. 254–262.",
    "M. Lanvin, P.-F. Gimenez, Y. Han, F. Majorczyk, L. Mé, E. Totel, "
      + "Errors in the CICIDS2017 dataset and the significant differences "
      + "in detection performances it makes, in: International Conference "
      + "on Risks and Security of Internet and Systems (CRiSIS), Springer, "
      + "2022, pp. 18–33.",
    // -------- Agents LLM offensifs / SOC 2023-2025 (53-55)
    "G. Deng, Y. Liu, V. Mayoral-Vilches, P. Liu, Y. Li, Y. Xu, "
      + "T. Zhang, Y. Liu, M. Pinzger, S. Rass, PentestGPT: An "
      + "LLM-empowered automatic penetration testing tool, in: USENIX "
      + "Security Symposium, 2024.",
    "A. Happe, J. Cito, Getting pwn'd by AI: Penetration testing with "
      + "large language models, in: ACM Joint European Software "
      + "Engineering Conference and Symposium on the Foundations of "
      + "Software Engineering (ESEC/FSE), 2023, pp. 2082–2086.",
    "S. Srinivas, B. Kirk, J. Zendejas, M. Espino, M. Boskovich, "
      + "A. Bari, K. Dajani, N. Alzahrani, AI-augmented SOC: A survey of "
      + "LLMs and agents for security automation, Journal of "
      + "Cybersecurity and Privacy 5 (4) (2025) 95.",
    // -------- Travaux antérieurs des auteurs (56)
    "M. A. E. Bahri, F. Jemili, O. Korbaa, Comparative study between ML "
      + "approaches in intrusion detection context, in: 2023 IEEE "
      + "Afro-Mediterranean Conference on Artificial Intelligence "
      + "(AMCAI), Hammamet, Tunisia, 2023, pp. 1–6, "
      + "doi:10.1109/AMCAI59331.2023.10431511.",
    // -------- Blockchain + multi-agent + agentic IDS (57-76) --------
    "C. Liang, B. Shanmugam, S. Azam, A. Karim, A. Islam, M. Zamani, "
      + "N. B. Idris, Intrusion detection system for the Internet of Things "
      + "based on blockchain and multi-agent systems, Electronics 9 (7) "
      + "(2020) 1120.",
    "M. Soltani, K. Khajavi, M. J. Siavoshani, A. H. Jahangir, A "
      + "multi-agent adaptive deep learning framework for online intrusion "
      + "detection, Cybersecurity 6 (2023) 44.",
    "A. Ali, et al., Federated learning-enhanced blockchain framework for "
      + "privacy-preserving intrusion detection in industrial IoT, "
      + "arXiv:2505.15376 (2025).",
    "K. Begum, et al., BFLIDS: Blockchain-driven federated learning for "
      + "intrusion detection in IoMT networks, Sensors 24 (14) (2024) 4591.",
    "H. Nandanwar, R. Katarya, A hybrid blockchain-based framework for "
      + "securing intrusion detection systems in the Internet of Things, "
      + "Cluster Computing 28 (2025).",
    "A. Kumar, B. Sharma, A. Noonia, Secure blockchain-based intrusion "
      + "detection for IoT networks, Discover Computing 28 (2025).",
    "H. Li, et al., Multi-agent collaborative intrusion detection for "
      + "low-altitude economy IoT: an LLM-enhanced agentic AI framework, "
      + "arXiv:2601.17817 (2026).",
    "S. J. Lazer, K. Aryal, M. Gupta, E. Bertino, A survey of agentic AI "
      + "and cybersecurity: challenges, opportunities and use-case "
      + "prototypes, arXiv:2601.05293 (2026).",
    "D. Gosmar, D. A. Dahl, Sentinel agents for secure and trustworthy "
      + "agentic AI in multi-agent systems, arXiv:2509.14956 (2025).",
    "P. Zambare, V. N. Thanikella, N. P. Kottur, et al., NetMoniAI: an "
      + "agentic AI framework for network security and monitoring, "
      + "arXiv:2508.10052 (2025).",
    "A. Jin, Y. Ye, B. Lee, Y. Qiao, DeCoAgent: large language model "
      + "empowered decentralized autonomous collaboration agents based on "
      + "smart contracts, IEEE Access 12 (2024), "
      + "doi:10.1109/ACCESS.2024.3481641.",
    "M. Qi, T. Zhu, L. Zhang, N. Li, W. Zhou, Towards transparent and "
      + "incentive-compatible collaboration in decentralized LLM multi-agent "
      + "systems: a blockchain-driven approach, arXiv:2509.16736 (2025).",
    "X. Li, et al., BlockAgents: towards Byzantine-robust LLM-based "
      + "multi-agent coordination via blockchain, in: Proc. ACM TURC "
      + "Conference, 2024, doi:10.1145/3674399.3674445.",
    "A. Capponi, A. Gliozzo, C. Han, J. Lee, DAO-AI: evaluating collective "
      + "decision-making through agentic AI in decentralized governance, "
      + "arXiv:2510.21117 (2025).",
    "K. Lad, M. A. A. Dewan, F. Lin, Trust management for multi-agent "
      + "systems using smart contracts, Athabasca University, 2020.",
    "A. Kott (Ed.), Autonomous Intelligent Cyber Defense Agent (AICA): A "
      + "Comprehensive Guide, Springer, 2023.",
    "T. T. Nguyen, V. J. Reddi, Deep reinforcement learning for cyber "
      + "security, IEEE Transactions on Neural Networks and Learning Systems "
      + "34 (8) (2023) 3779–3795.",
    "H. Aydin, M. A. Aydin, A multi-agent-based DDoS detection and defense "
      + "system design with federated learning and blockchain in a public "
      + "cloud network environment, Cluster Computing 28 (2025).",
    "C. S. de Witt, Open challenges in multi-agent security: towards secure "
      + "systems of interacting AI agents, arXiv:2505.02077 (2025).",
    "V. Vinay, The evolution of agentic AI in cybersecurity: from single "
      + "LLM reasoners to multi-agent systems and autonomous pipelines, "
      + "arXiv:2512.06659 (2025).",
  ];

  const items = [
    h1("References"),
  ];
  refs.forEach((ref, idx) => {
    items.push(new (require("docx").Paragraph)({
      alignment: require("docx").AlignmentType.JUSTIFIED,
      spacing: { after: 60 },
      children: [
        new (require("docx").TextRun)({ text: `[${idx + 1}] `, bold: true,
          size: 18 }),
        new (require("docx").TextRun)({ text: ref, size: 18 }),
      ],
    }));
  });
  return items;
};
