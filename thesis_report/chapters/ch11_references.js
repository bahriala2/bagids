/* Section (fin) — References.
 * NB : entrées à vérifier / reformater au style Elsevier avant soumission
 * (années, pages, DOI). Tous les travaux cités sont réels et bien établis. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => {
  const refs = [
    "C. Yin, Y. Zhu, J. Fei, X. He, A deep learning approach for intrusion "
      + "detection using recurrent neural networks, IEEE Access 5 (2017) "
      + "21954–21961.",
    "P. Vinayakumar, M. Alazab, K. P. Soman, P. Poornachandran, A. Al-Nemrat, "
      + "S. Venkatraman, Deep learning approach for intelligent intrusion "
      + "detection system, IEEE Access 7 (2019) 41525–41550.",
    "N. Shone, T. N. Ngoc, V. D. Phai, Q. Shi, A deep learning approach to "
      + "network intrusion detection, IEEE Transactions on Emerging Topics in "
      + "Computational Intelligence 2 (1) (2018) 41–50.",
    "A. Javaid, Q. Niyaz, W. Sun, M. Alam, A deep learning approach for "
      + "network intrusion detection system, in: EAI International Conference "
      + "on Bio-inspired Information and Communications Technologies (BICT), "
      + "2016.",
    "H. Liu, B. Lang, Machine learning and deep learning methods for "
      + "intrusion detection systems: A survey, Applied Sciences 9 (20) (2019) "
      + "4396.",
    "I. Sharafaldin, A. H. Lashkari, A. A. Ghorbani, Toward generating a new "
      + "intrusion detection dataset and intrusion traffic characterization, "
      + "in: 4th International Conference on Information Systems Security and "
      + "Privacy (ICISSP), 2018, pp. 108–116.",
    "G. Folino, P. Sabatino, Ensemble based collaborative and distributed "
      + "intrusion detection systems: A survey, Journal of Network and "
      + "Computer Applications 66 (2016) 1–16.",
    "B. A. Tama, M. Comuzzi, K.-H. Rhee, TSE-IDS: A two-stage classifier "
      + "ensemble for intelligent anomaly-based intrusion detection system, "
      + "IEEE Access 7 (2019) 94497–94507.",
    "C. Guo, G. Pleiss, Y. Sun, K. Q. Weinberger, On calibration of modern "
      + "neural networks, in: International Conference on Machine Learning "
      + "(ICML), 2017, pp. 1321–1330.",
    "Y. Geifman, R. El-Yaniv, Selective classification for deep neural "
      + "networks, in: Advances in Neural Information Processing Systems "
      + "(NeurIPS), 2017.",
    "B. Biggio, F. Roli, Wild patterns: Ten years after the rise of "
      + "adversarial machine learning, Pattern Recognition 84 (2018) 317–331.",
    "N. Papernot, P. McDaniel, A. Sinha, M. P. Wellman, SoK: Security and "
      + "privacy in machine learning, in: IEEE European Symposium on Security "
      + "and Privacy (EuroS&P), 2018, pp. 399–414.",
    "M. Jagielski, A. Oprea, B. Biggio, C. Liu, C. Nita-Rotaru, B. Li, "
      + "Manipulating machine learning: Poisoning attacks and countermeasures "
      + "for regression learning, in: IEEE Symposium on Security and Privacy "
      + "(S&P), 2018, pp. 19–35.",
    "T. Gu, K. Liu, B. Dolan-Gavitt, S. Garg, BadNets: Evaluating "
      + "backdooring attacks on deep neural networks, IEEE Access 7 (2019) "
      + "47230–47244.",
    "O. Ibitoye, R. Abou-Khamis, A. Matrawy, M. O. Shafiq, The threat of "
      + "adversarial attacks on machine learning in network security: A "
      + "survey, arXiv:1911.02621 (2019).",
    "E. H. Spafford, D. Zamboni, Intrusion detection using autonomous "
      + "agents, Computer Networks 34 (4) (2000) 547–570.",
    "Á. Herrero, E. Corchado, Multiagent systems for network intrusion "
      + "detection: A review, in: Computational Intelligence in Security for "
      + "Information Systems (CISIS), Springer, 2009, pp. 143–154.",
    "W. Li, W. Meng, L. F. Kwok, Surveying trust-based collaborative "
      + "intrusion detection: State-of-the-art, challenges and future "
      + "directions, IEEE Communications Surveys & Tutorials 24 (1) (2022) "
      + "280–305.",
    "N. Alexopoulos, E. Vasilomanolakis, N. R. Ivanko, M. Mühlhäuser, "
      + "Towards blockchain-based collaborative intrusion detection systems, "
      + "in: International Conference on Critical Information Infrastructures "
      + "Security (CRITIS), Springer, 2017, pp. 107–118.",
    "T. Golomb, Y. Mirsky, Y. Elovici, CIoTA: Collaborative IoT anomaly "
      + "detection via blockchain, in: Workshop on Decentralized IoT Security "
      + "and Standards (DISS), 2018.",
    "W. Meng, E. W. Tischhauser, Q. Wang, Y. Wang, J. Han, When intrusion "
      + "detection meets blockchain technology: A review, IEEE Access 6 "
      + "(2018) 10179–10188.",
    "E. Androulaki, A. Barger, V. Bortnikov, C. Cachin, K. Christidis, et "
      + "al., Hyperledger Fabric: A distributed operating system for "
      + "permissioned blockchains, in: EuroSys, 2018, pp. 30:1–30:15.",
    "D. Preuveneers, V. Rimmer, I. Tsingenopoulos, J. Spooren, W. Joosen, "
      + "E. Ilie-Zudor, Chained anomaly detection models for federated "
      + "learning: An intrusion detection case study, Applied Sciences 8 (12) "
      + "(2018) 2663.",
    "S. Rathore, B. W. Kwon, J. H. Park, BlockSecIoTNet: Blockchain-based "
      + "decentralized security architecture for IoT network, Journal of "
      + "Network and Computer Applications 143 (2019) 167–177.",
    "M. A. Ferrag, F. Alwahedi, A. Battah, B. Cherif, A. Mechri, N. Tihanyi, "
      + "Generative AI and large language models for cyber security: All "
      + "insights you need, arXiv:2405.12750 (2024).",
    "J. Zhang, H. Bu, H. Wen, Y. Liu, H. Fei, et al., When LLMs meet "
      + "cybersecurity: A systematic literature review, Cybersecurity 8 "
      + "(2025).",
    "Y. Yao, J. Duan, K. Xu, Y. Cai, Z. Sun, Y. Zhang, A survey on large "
      + "language model (LLM) security and privacy: The good, the bad, and "
      + "the ugly, High-Confidence Computing 4 (2) (2024) 100211.",
    "R. C. Arkin, Behavior-Based Robotics, MIT Press, 1998.",
  ];

  const items = [
    h1("Bibliography"),
    p([r("Note: bibliographic entries below cite established works and are to "
        + "be verified and reformatted to the Elsevier numbered style "
        + "(volume, pages, DOI) prior to submission.")]),
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
