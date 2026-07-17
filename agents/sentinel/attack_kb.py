"""
BAg-IDS — Base de connaissances analyste pour l'aide à la décision (XAI).

Pour chaque classe d'attaque CICIDS2017 déployée : ce qu'est l'attaque,
comment les features réseau typiques la trahissent, ce que l'analyste doit
vérifier AVANT d'approuver la remédiation, et les causes connues de faux
positifs. Trilingue (en/fr/ar) pour la console HITL.

Cette base est DÉTERMINISTE : elle garantit une aide à la décision riche
même sans backend LLM (le LLM, quand il est disponible, particularise ce
socle avec les attributions SHAP du flux concerné, il ne le remplace pas).

`fp_risk` : propension connue de la classe aux faux positifs (low/medium/
high) — entre dans la recommandation consultative.
"""

from __future__ import annotations

KB: dict[str, dict] = {
    "DDoS": {
        "fp_risk": "medium",
        "what": {
            "en": "Distributed denial of service: many sources flood one "
                  "service to exhaust bandwidth or connection capacity.",
            "fr": "Déni de service distribué : de nombreuses sources "
                  "saturent un service pour épuiser sa bande passante ou sa "
                  "capacité de connexions.",
            "ar": "حجب خدمة موزَّع: مصادر عديدة تُغرق خدمة واحدة لاستنزاف "
                  "النطاق الترددي أو سعة الاتصالات.",
        },
        "signals": {
            "en": "High packet and flow rates towards a single destination, "
                  "small or uniform packet sizes, and elevated ACK/SYN flag "
                  "counts are the classic flood signature.",
            "fr": "Des débits de paquets et de flux élevés vers une même "
                  "destination, des paquets petits ou de taille uniforme et "
                  "des compteurs de drapeaux ACK/SYN élevés forment la "
                  "signature classique d'une inondation.",
            "ar": "معدلات حزم وتدفقات مرتفعة نحو وجهة واحدة، وحزم صغيرة أو "
                  "موحّدة الحجم، وارتفاع عدّادات أعلام ACK/SYN هي البصمة "
                  "الكلاسيكية للإغراق.",
        },
        "checks": {
            "en": ["Count concurrent flows towards the same destination "
                   "service and compare with its baseline",
                   "Check the target service's latency and availability "
                   "(is there real degradation?)",
                   "Look at source diversity: a flash crowd (legitimate "
                   "traffic spike) comes with plausible user behaviour, "
                   "a DDoS does not"],
            "fr": ["Compter les flux simultanés vers le même service cible "
                   "et comparer à sa charge habituelle",
                   "Vérifier la latence et la disponibilité du service visé "
                   "(y a-t-il une dégradation réelle ?)",
                   "Examiner la diversité des sources : un pic légitime "
                   "(flash crowd) s'accompagne d'un comportement utilisateur "
                   "plausible, un DDoS non"],
            "ar": ["عدّ التدفقات المتزامنة نحو الخدمة الهدف ومقارنتها "
                   "بحملها المعتاد",
                   "التحقق من زمن استجابة الخدمة المستهدفة وتوفرها (هل يوجد "
                   "تدهور فعلي؟)",
                   "فحص تنوع المصادر: الذروة المشروعة تصاحبها سلوكيات "
                   "مستخدمين معقولة، بخلاف هجوم DDoS"],
        },
        "fp_notes": {
            "en": "Flash crowds, load tests and scheduled backup jobs are "
                  "the usual false-positive causes for this class.",
            "fr": "Les pics d'affluence légitimes, les tests de charge et "
                  "les sauvegardes planifiées sont les causes habituelles de "
                  "faux positifs pour cette classe.",
            "ar": "ذروات الزيارات المشروعة واختبارات الحمل والنسخ الاحتياطي "
                  "المجدول هي الأسباب المعتادة للإنذارات الكاذبة هنا.",
        },
    },
    "DoS_Hulk": {
        "fp_risk": "medium",
        "what": {
            "en": "HTTP flood (Hulk tool): a barrage of unique, randomised "
                  "HTTP requests designed to bypass caches and exhaust the "
                  "web server.",
            "fr": "Inondation HTTP (outil Hulk) : un déluge de requêtes HTTP "
                  "uniques et aléatoires conçu pour contourner les caches et "
                  "épuiser le serveur web.",
            "ar": "إغراق HTTP (أداة Hulk): وابل من طلبات HTTP فريدة وعشوائية "
                  "مصمَّم لتجاوز الذاكرة المؤقتة وإنهاك خادم الويب.",
        },
        "signals": {
            "en": "Small packets at a high rate, short inter-arrival times "
                  "with bursty variance, and many short-lived flows to the "
                  "web port betray the request flood.",
            "fr": "Des petits paquets à haut débit, des temps inter-arrivée "
                  "courts à la variance en rafales et de nombreux flux brefs "
                  "vers le port web trahissent l'inondation de requêtes.",
            "ar": "حزم صغيرة بمعدل مرتفع، وأزمنة وصول بينية قصيرة متقلبة، "
                  "وتدفقات قصيرة عديدة نحو منفذ الويب تكشف إغراق الطلبات.",
        },
        "checks": {
            "en": ["Inspect web server access logs for bursts of GET "
                   "requests with randomised URLs or query strings",
                   "Check web server CPU, memory and worker-pool saturation",
                   "Confirm the source is not a benchmarking or monitoring "
                   "tool run by your own teams"],
            "fr": ["Inspecter les logs du serveur web : rafales de GET avec "
                   "des URL ou paramètres aléatoires",
                   "Vérifier le CPU, la mémoire et la saturation des workers "
                   "du serveur web",
                   "Confirmer que la source n'est pas un outil de bench ou "
                   "de supervision interne"],
            "ar": ["فحص سجلات خادم الويب بحثًا عن دفعات طلبات GET بعناوين أو "
                   "معاملات عشوائية",
                   "التحقق من المعالج والذاكرة وتشبع مجمع العمّال في الخادم",
                   "التأكد من أن المصدر ليس أداة قياس أو مراقبة داخلية"],
        },
        "fp_notes": {
            "en": "Benchmark tools and aggressive health-check probes can "
                  "mimic this pattern.",
            "fr": "Les outils de bench et les sondes de supervision "
                  "agressives peuvent imiter ce motif.",
            "ar": "أدوات القياس وفحوصات الصحة العدوانية قد تحاكي هذا النمط.",
        },
    },
    "DoS_GoldenEye": {
        "fp_risk": "medium",
        "what": {
            "en": "HTTP denial of service (GoldenEye tool): floods of "
                  "keep-alive GET requests holding many concurrent "
                  "connections open on the web server.",
            "fr": "Déni de service HTTP (outil GoldenEye) : rafales de "
                  "requêtes GET keep-alive qui maintiennent ouvertes de "
                  "nombreuses connexions simultanées sur le serveur web.",
            "ar": "حجب خدمة HTTP (أداة GoldenEye): دفعات من طلبات GET مع "
                  "keep-alive تُبقي اتصالات متزامنة كثيرة مفتوحة على الخادم.",
        },
        "signals": {
            "en": "Many concurrent medium-lived flows to the web port, "
                  "keep-alive misuse (long flows with periodic small "
                  "requests) and bursty inter-arrival times.",
            "fr": "De nombreux flux simultanés de durée moyenne vers le port "
                  "web, un détournement du keep-alive (flux longs avec "
                  "petites requêtes périodiques) et des temps inter-arrivée "
                  "en rafales.",
            "ar": "تدفقات متزامنة عديدة متوسطة العمر نحو منفذ الويب، وإساءة "
                  "استخدام keep-alive، وأزمنة وصول بينية متقطعة.",
        },
        "checks": {
            "en": ["Check the web server's connection pool / open-socket "
                   "count against its limits",
                   "Look for repeated GET requests with rotating user-agents "
                   "or random no-cache headers in access logs",
                   "Verify whether legitimate crawlers or scrapers are "
                   "active on the site"],
            "fr": ["Vérifier le pool de connexions / sockets ouverts du "
                   "serveur web par rapport à ses limites",
                   "Chercher dans les logs des GET répétés avec user-agents "
                   "tournants ou en-têtes no-cache aléatoires",
                   "Vérifier si des crawlers ou scrapers légitimes sont "
                   "actifs sur le site"],
            "ar": ["التحقق من مجمع الاتصالات/المقابس المفتوحة في الخادم "
                   "مقارنة بحدوده",
                   "البحث في السجلات عن طلبات GET متكررة بوكلاء مستخدم "
                   "متبدلين أو ترويسات no-cache عشوائية",
                   "التحقق من نشاط زواحف أو أدوات كشط مشروعة على الموقع"],
        },
        "fp_notes": {
            "en": "Aggressive but legitimate crawlers are the main "
                  "false-positive source.",
            "fr": "Les crawlers agressifs mais légitimes sont la principale "
                  "source de faux positifs.",
            "ar": "الزواحف العدوانية لكنها مشروعة هي المصدر الرئيس للإنذارات "
                  "الكاذبة.",
        },
    },
    "DoS_slowloris": {
        "fp_risk": "medium",
        "what": {
            "en": "Slowloris: opens many HTTP connections and keeps them "
                  "alive by sending partial headers very slowly, starving "
                  "the server's connection table.",
            "fr": "Slowloris : ouvre de nombreuses connexions HTTP et les "
                  "maintient en vie en envoyant très lentement des en-têtes "
                  "partiels, jusqu'à épuiser la table de connexions du "
                  "serveur.",
            "ar": "Slowloris: يفتح اتصالات HTTP عديدة ويبقيها حية بإرسال "
                  "ترويسات جزئية ببطء شديد حتى تستنفد جدول اتصالات الخادم.",
        },
        "signals": {
            "en": "Very long flow durations with almost no payload, large "
                  "maximum inter-arrival times and high idle times are the "
                  "slow-attack fingerprint.",
            "fr": "Des flux de très longue durée quasiment sans charge "
                  "utile, des temps inter-arrivée maximaux très grands et "
                  "des temps d'inactivité élevés : c'est l'empreinte des "
                  "attaques lentes.",
            "ar": "تدفقات طويلة جدًا بلا حمولة تقريبًا، وأزمنة وصول بينية "
                  "قصوى كبيرة، وأزمنة خمول عالية: هذه بصمة الهجمات البطيئة.",
        },
        "checks": {
            "en": ["Count half-open / stalled HTTP connections per source IP",
                   "Check the web server's connection timeout configuration",
                   "Rule out long-polling, Server-Sent Events or WebSocket "
                   "endpoints, which legitimately hold long quiet "
                   "connections"],
            "fr": ["Compter les connexions HTTP semi-ouvertes ou bloquées "
                   "par IP source",
                   "Vérifier la configuration des timeouts du serveur web",
                   "Écarter le long-polling, les Server-Sent Events ou les "
                   "WebSockets, qui maintiennent légitimement de longues "
                   "connexions silencieuses"],
            "ar": ["عدّ الاتصالات نصف المفتوحة أو المتوقفة لكل عنوان مصدر",
                   "التحقق من إعدادات مهلات خادم الويب",
                   "استبعاد long-polling وSSE وWebSocket التي تُبقي اتصالات "
                   "طويلة هادئة بشكل مشروع"],
        },
        "fp_notes": {
            "en": "Long-polling applications and clients on very slow links "
                  "look similar at flow level.",
            "fr": "Les applications en long-polling et les clients sur "
                  "liaisons très lentes ressemblent à ce motif au niveau "
                  "flux.",
            "ar": "تطبيقات long-polling والعملاء على وصلات بطيئة جدًا "
                  "يشبهون هذا النمط على مستوى التدفق.",
        },
    },
    "DoS_Slowhttptest": {
        "fp_risk": "medium",
        "what": {
            "en": "Slow HTTP attack (slowhttptest tool): sends request "
                  "headers or body at a crawl to hold server threads busy "
                  "(slowloris/slow-body family).",
            "fr": "Attaque HTTP lente (outil slowhttptest) : envoie les "
                  "en-têtes ou le corps de requête au compte-gouttes pour "
                  "occuper les threads du serveur (famille slowloris/slow "
                  "body).",
            "ar": "هجوم HTTP بطيء (أداة slowhttptest): يرسل الترويسات أو "
                  "جسم الطلب ببطء شديد لإشغال خيوط الخادم.",
        },
        "signals": {
            "en": "Long, low-rate flows with tiny forward packets, high "
                  "idle and inter-arrival extremes, similar to slowloris.",
            "fr": "Flux longs à faible débit avec de minuscules paquets "
                  "montants, des extrêmes d'inactivité et d'inter-arrivée "
                  "élevés, proches de slowloris.",
            "ar": "تدفقات طويلة منخفضة المعدل بحزم أمامية ضئيلة وقيم خمول "
                  "قصوى، قريبة من Slowloris.",
        },
        "checks": {
            "en": ["Inspect the server's active connection table for "
                   "requests stuck in header/body reception",
                   "Check whether minimum-rate protections (e.g. "
                   "mod_reqtimeout) are configured",
                   "Rule out legitimate slow clients (mobile, satellite, "
                   "IoT devices)"],
            "fr": ["Inspecter la table des connexions actives du serveur : "
                   "requêtes bloquées en réception d'en-têtes/corps",
                   "Vérifier si des protections de débit minimal (ex. "
                   "mod_reqtimeout) sont configurées",
                   "Écarter les clients légitimement lents (mobile, "
                   "satellite, objets connectés)"],
            "ar": ["فحص جدول الاتصالات النشطة للخادم: طلبات عالقة في استقبال "
                   "الترويسات أو الجسم",
                   "التحقق من وجود حماية بحد أدنى للمعدل (مثل mod_reqtimeout)",
                   "استبعاد العملاء البطيئين بشكل مشروع (جوال، أقمار، إنترنت "
                   "الأشياء)"],
        },
        "fp_notes": {
            "en": "IoT devices and clients behind degraded links can "
                  "legitimately produce very slow requests.",
            "fr": "Les objets connectés et les clients derrière des liens "
                  "dégradés peuvent produire des requêtes très lentes de "
                  "façon légitime.",
            "ar": "أجهزة إنترنت الأشياء والعملاء خلف وصلات متدهورة قد ينتجون "
                  "طلبات بطيئة جدًا بشكل مشروع.",
        },
    },
    "PortScan": {
        "fp_risk": "high",
        "what": {
            "en": "Reconnaissance: a source probes many ports to map "
                  "exposed services before an actual attack.",
            "fr": "Reconnaissance : une source sonde de nombreux ports pour "
                  "cartographier les services exposés avant une attaque "
                  "réelle.",
            "ar": "استطلاع: مصدر يفحص منافذ عديدة لرسم خريطة الخدمات "
                  "المكشوفة قبل هجوم فعلي.",
        },
        "signals": {
            "en": "Many tiny, short flows to different ports, SYN probes "
                  "without completed handshakes and near-zero payload are "
                  "the scanning signature.",
            "fr": "De très nombreux petits flux brefs vers des ports "
                  "différents, des sondes SYN sans poignée de main complète "
                  "et une charge utile quasi nulle : c'est la signature du "
                  "scan.",
            "ar": "تدفقات صغيرة وقصيرة كثيرة نحو منافذ مختلفة، ومسابر SYN "
                  "دون مصافحة مكتملة، وحمولة شبه معدومة: بصمة المسح.",
        },
        "checks": {
            "en": ["Count distinct destination ports touched by this source "
                   "in the last minutes",
                   "Check whether the source is a KNOWN internal scanner "
                   "(vulnerability scanner, asset discovery, monitoring)",
                   "If external: check source reputation and whether "
                   "sensitive ports (22, 3389, 445) were probed"],
            "fr": ["Compter les ports de destination distincts touchés par "
                   "cette source dans les dernières minutes",
                   "Vérifier si la source est un scanner interne CONNU "
                   "(scanner de vulnérabilités, découverte d'actifs, "
                   "supervision)",
                   "Si externe : vérifier la réputation de la source et si "
                   "des ports sensibles (22, 3389, 445) ont été sondés"],
            "ar": ["عدّ منافذ الوجهة المختلفة التي لمسها هذا المصدر في "
                   "الدقائق الأخيرة",
                   "التحقق مما إذا كان المصدر ماسحًا داخليًا معروفًا (فحص "
                   "ثغرات، اكتشاف أصول، مراقبة)",
                   "إن كان خارجيًا: فحص سمعة المصدر وما إذا فُحصت منافذ "
                   "حساسة (22، 3389، 445)"],
        },
        "fp_notes": {
            "en": "Authorised vulnerability scanners and monitoring tools "
                  "are the most common false positive: whitelist them "
                  "instead of blocking.",
            "fr": "Les scanners de vulnérabilités autorisés et les outils de "
                  "supervision sont le faux positif le plus fréquent : les "
                  "mettre en liste blanche plutôt que les bloquer.",
            "ar": "ماسحات الثغرات المصرَّح بها وأدوات المراقبة هي أكثر "
                  "الإنذارات الكاذبة شيوعًا: أضفها لقائمة السماح بدل الحظر.",
        },
    },
    "Bot": {
        "fp_risk": "high",
        "what": {
            "en": "Botnet activity: an infected internal host periodically "
                  "contacts a command-and-control (C2) server for orders.",
            "fr": "Activité de botnet : un hôte interne infecté contacte "
                  "périodiquement un serveur de commande et contrôle (C2) "
                  "pour recevoir des ordres.",
            "ar": "نشاط بوت نت: مضيف داخلي مصاب يتصل دوريًا بخادم قيادة "
                  "وتحكم (C2) لتلقي الأوامر.",
        },
        "signals": {
            "en": "Small periodic flows with regular inter-arrival times "
                  "(beaconing) towards the same external destination are "
                  "the C2 heartbeat pattern.",
            "fr": "De petits flux périodiques aux temps inter-arrivée "
                  "réguliers (beaconing) vers la même destination externe : "
                  "c'est le battement de cœur d'un C2.",
            "ar": "تدفقات صغيرة دورية بأزمنة وصول منتظمة (نبض) نحو الوجهة "
                  "الخارجية نفسها: هذا نبض خادم C2.",
        },
        "checks": {
            "en": ["Check the destination IP/domain against threat "
                   "intelligence (known C2 lists)",
                   "Pull the EDR/antivirus status of the internal source "
                   "host",
                   "Look for other flows from the same host (lateral "
                   "movement, data staging)"],
            "fr": ["Vérifier l'IP/domaine de destination dans la threat "
                   "intelligence (listes C2 connues)",
                   "Consulter l'état EDR/antivirus de l'hôte source interne",
                   "Chercher d'autres flux du même hôte (mouvement latéral, "
                   "préparation d'exfiltration)"],
            "ar": ["فحص عنوان/نطاق الوجهة في قواعد استخبارات التهديد (قوائم "
                   "C2 المعروفة)",
                   "مراجعة حالة EDR/مضاد الفيروسات للمضيف المصدر الداخلي",
                   "البحث عن تدفقات أخرى من المضيف نفسه (حركة جانبية، تجهيز "
                   "تسريب)"],
        },
        "fp_notes": {
            "en": "Legitimate periodic keepalives (NTP, telemetry, chat and "
                  "update agents) beacon too — verify the destination "
                  "before isolating a host.",
            "fr": "Les keepalives légitimes (NTP, télémétrie, messageries, "
                  "agents de mise à jour) émettent aussi périodiquement — "
                  "vérifier la destination avant d'isoler un hôte.",
            "ar": "النبضات الدورية المشروعة (NTP، القياس عن بعد، المراسلة، "
                  "وكلاء التحديث) تنبض أيضًا — تحقق من الوجهة قبل عزل "
                  "المضيف.",
        },
    },
    "FTPPatator": {
        "fp_risk": "low",
        "what": {
            "en": "FTP brute force (Patator tool): automated password "
                  "guessing against an FTP service.",
            "fr": "Force brute FTP (outil Patator) : essais automatisés de "
                  "mots de passe contre un service FTP.",
            "ar": "قوة غاشمة على FTP (أداة Patator): تخمين آلي لكلمات المرور "
                  "ضد خدمة FTP.",
        },
        "signals": {
            "en": "Many short, similar flows to port 21 with regular timing "
                  "and small packets: one login attempt per flow.",
            "fr": "De nombreux flux courts et similaires vers le port 21, au "
                  "rythme régulier et aux petits paquets : une tentative de "
                  "connexion par flux.",
            "ar": "تدفقات قصيرة متشابهة كثيرة نحو المنفذ 21 بإيقاع منتظم "
                  "وحزم صغيرة: محاولة دخول لكل تدفق.",
        },
        "checks": {
            "en": ["Check FTP server logs: failed login count per source IP",
                   "Verify whether targeted accounts got locked out",
                   "Rule out a misconfigured sync/backup script using stale "
                   "credentials"],
            "fr": ["Vérifier les logs du serveur FTP : nombre d'échecs de "
                   "connexion par IP source",
                   "Vérifier si des comptes ciblés ont été verrouillés",
                   "Écarter un script de synchronisation/sauvegarde mal "
                   "configuré utilisant des identifiants périmés"],
            "ar": ["فحص سجلات خادم FTP: عدد محاولات الدخول الفاشلة لكل مصدر",
                   "التحقق من قفل الحسابات المستهدفة",
                   "استبعاد سكربت مزامنة/نسخ احتياطي بمعلومات دخول قديمة"],
        },
        "fp_notes": {
            "en": "Automation retrying with expired credentials is the "
                  "typical benign cause; blocking one source IP has a small "
                  "blast radius.",
            "fr": "Une automatisation qui réessaie avec des identifiants "
                  "expirés est la cause bénigne typique ; bloquer une IP "
                  "source a un impact limité.",
            "ar": "الأتمتة التي تعيد المحاولة ببيانات منتهية هي السبب الحميد "
                  "المعتاد؛ حظر عنوان مصدر واحد أثره محدود.",
        },
    },
    "SSHPatator": {
        "fp_risk": "low",
        "what": {
            "en": "SSH brute force (Patator tool): automated password "
                  "guessing against an SSH service.",
            "fr": "Force brute SSH (outil Patator) : essais automatisés de "
                  "mots de passe contre un service SSH.",
            "ar": "قوة غاشمة على SSH (أداة Patator): تخمين آلي لكلمات المرور "
                  "ضد خدمة SSH.",
        },
        "signals": {
            "en": "Repeated short sessions to port 22 with near-identical "
                  "packet sizes and regular inter-arrival times: scripted "
                  "login attempts.",
            "fr": "Des sessions courtes répétées vers le port 22, aux "
                  "tailles de paquets quasi identiques et aux temps "
                  "inter-arrivée réguliers : tentatives de connexion "
                  "scriptées.",
            "ar": "جلسات قصيرة متكررة نحو المنفذ 22 بأحجام حزم شبه متطابقة "
                  "وأزمنة منتظمة: محاولات دخول مبرمجة.",
        },
        "checks": {
            "en": ["Check sshd auth logs (failed password / invalid user "
                   "entries per source)",
                   "Verify fail2ban or equivalent has not already banned "
                   "the source",
                   "Check the source: internal automation with stale keys "
                   "also produces auth failures"],
            "fr": ["Vérifier les logs d'authentification sshd (échecs de mot "
                   "de passe / utilisateurs invalides par source)",
                   "Vérifier que fail2ban ou équivalent n'a pas déjà banni "
                   "la source",
                   "Vérifier la source : une automatisation interne avec des "
                   "clés périmées produit aussi des échecs d'authentification"],
            "ar": ["فحص سجلات مصادقة sshd (فشل كلمة المرور/مستخدم غير صالح "
                   "لكل مصدر)",
                   "التحقق من أن fail2ban أو ما يعادله لم يحظر المصدر بالفعل",
                   "فحص المصدر: الأتمتة الداخلية بمفاتيح قديمة تنتج أيضًا "
                   "إخفاقات مصادقة"],
        },
        "fp_notes": {
            "en": "Internal automation with rotated-out credentials is the "
                  "main benign look-alike.",
            "fr": "L'automatisation interne avec des identifiants révoqués "
                  "est le principal sosie bénin.",
            "ar": "الأتمتة الداخلية ببيانات اعتماد ملغاة هي الشبيه الحميد "
                  "الرئيس.",
        },
    },
    "Heartbleed": {
        "fp_risk": "low",
        "what": {
            "en": "Heartbleed (CVE-2014-0160): exploits the TLS heartbeat "
                  "extension to read server memory, potentially leaking "
                  "keys and credentials.",
            "fr": "Heartbleed (CVE-2014-0160) : exploite l'extension TLS "
                  "heartbeat pour lire la mémoire du serveur et "
                  "potentiellement exfiltrer clés et identifiants.",
            "ar": "Heartbleed (CVE-2014-0160): يستغل امتداد نبض TLS لقراءة "
                  "ذاكرة الخادم وربما تسريب المفاتيح وبيانات الاعتماد.",
        },
        "signals": {
            "en": "Anomalously large backward payloads from the TLS port "
                  "(the leaked memory) against tiny forward requests are "
                  "the tell-tale asymmetry.",
            "fr": "Des charges utiles descendantes anormalement grandes "
                  "depuis le port TLS (la mémoire divulguée) face à de "
                  "minuscules requêtes montantes : l'asymétrie révélatrice.",
            "ar": "حمولات راجعة كبيرة بشكل شاذ من منفذ TLS (الذاكرة المسربة) "
                  "مقابل طلبات أمامية ضئيلة: عدم التماثل الكاشف.",
        },
        "checks": {
            "en": ["Check the target server's OpenSSL version (vulnerable: "
                   "1.0.1 to 1.0.1f)",
                   "Inspect TLS telemetry for oversized heartbeat responses",
                   "If confirmed: treat every secret on that host "
                   "(certificates, passwords) as compromised"],
            "fr": ["Vérifier la version OpenSSL du serveur cible "
                   "(vulnérable : 1.0.1 à 1.0.1f)",
                   "Inspecter la télémétrie TLS : réponses heartbeat "
                   "surdimensionnées",
                   "Si confirmé : considérer tous les secrets de cet hôte "
                   "(certificats, mots de passe) comme compromis"],
            "ar": ["التحقق من إصدار OpenSSL للخادم الهدف (الضعيف: 1.0.1 حتى "
                   "1.0.1f)",
                   "فحص قياسات TLS: استجابات نبض ضخمة",
                   "عند التأكيد: اعتبار كل أسرار المضيف (شهادات، كلمات مرور) "
                   "مخترقة"],
        },
        "fp_notes": {
            "en": "Rare in modern fleets (patched since 2014); a hit on a "
                  "patched server is almost certainly a false positive, on "
                  "an unpatched one it is critical.",
            "fr": "Rare sur les parcs modernes (corrigé depuis 2014) ; une "
                  "détection sur un serveur à jour est presque sûrement un "
                  "faux positif, sur un serveur non corrigé c'est critique.",
            "ar": "نادر في الأنظمة الحديثة (مرقّع منذ 2014)؛ الاكتشاف على "
                  "خادم محدث يكاد يكون إنذارًا كاذبًا، وعلى خادم غير مرقّع "
                  "يكون حرجًا.",
        },
    },
    "Infiltration": {
        "fp_risk": "high",
        "what": {
            "en": "Post-exploitation activity: an attacker already inside "
                  "the network pivots between hosts or accesses internal "
                  "resources.",
            "fr": "Activité post-exploitation : un attaquant déjà dans le "
                  "réseau pivote entre hôtes ou accède à des ressources "
                  "internes.",
            "ar": "نشاط ما بعد الاستغلال: مهاجم داخل الشبكة بالفعل يتنقل بين "
                  "المضيفين أو يصل إلى موارد داخلية.",
        },
        "signals": {
            "en": "Irregular internal flows on unusual ports, long "
                  "durations and atypical volumes; the pattern is subtle "
                  "and this class is known to be hard for flow-based "
                  "detectors.",
            "fr": "Des flux internes irréguliers sur des ports inhabituels, "
                  "de longues durées et des volumes atypiques ; le motif est "
                  "subtil et cette classe est connue pour être difficile "
                  "pour les détecteurs à base de flux.",
            "ar": "تدفقات داخلية غير منتظمة على منافذ غير معتادة، ومدد طويلة "
                  "وأحجام شاذة؛ النمط دقيق وهذه الفئة صعبة على كاشفات "
                  "التدفق.",
        },
        "checks": {
            "en": ["Pull EDR telemetry for both endpoints of the flow "
                   "(processes, users, recent logons)",
                   "Look for lateral-movement indicators (SMB/RDP/WinRM "
                   "between workstations)",
                   "Check outbound data volume from the source host "
                   "(exfiltration staging)"],
            "fr": ["Consulter la télémétrie EDR des deux extrémités du flux "
                   "(processus, utilisateurs, connexions récentes)",
                   "Chercher des indicateurs de mouvement latéral (SMB/RDP/"
                   "WinRM entre postes de travail)",
                   "Vérifier le volume de données sortant de l'hôte source "
                   "(préparation d'exfiltration)"],
            "ar": ["مراجعة قياسات EDR لطرفي التدفق (عمليات، مستخدمون، "
                   "تسجيلات دخول حديثة)",
                   "البحث عن مؤشرات الحركة الجانبية (SMB/RDP/WinRM بين "
                   "المحطات)",
                   "التحقق من حجم البيانات الصادرة من المضيف المصدر (تجهيز "
                   "تسريب)"],
        },
        "fp_notes": {
            "en": "Administrative tooling, backup agents and file "
                  "synchronisation regularly trigger this class; corroborate "
                  "with endpoint evidence before isolating.",
            "fr": "Les outils d'administration, agents de sauvegarde et "
                  "synchronisations de fichiers déclenchent régulièrement "
                  "cette classe ; corroborer avec des preuves côté poste "
                  "avant d'isoler.",
            "ar": "أدوات الإدارة ووكلاء النسخ الاحتياطي ومزامنة الملفات "
                  "تُطلق هذه الفئة كثيرًا؛ عزّز بأدلة من الجهاز قبل العزل.",
        },
    },
    "Web_AttackBrute_Force": {
        "fp_risk": "medium",
        "what": {
            "en": "Web login brute force: repeated authentication attempts "
                  "against a web application's login form or API.",
            "fr": "Force brute web : tentatives d'authentification répétées "
                  "contre le formulaire de connexion ou l'API d'une "
                  "application web.",
            "ar": "قوة غاشمة على الويب: محاولات مصادقة متكررة ضد نموذج دخول "
                  "تطبيق ويب أو واجهته البرمجية.",
        },
        "signals": {
            "en": "Repeated similar-sized POST flows to the web port with "
                  "regular timing: one credential guess per request.",
            "fr": "Des flux POST répétés de taille similaire vers le port "
                  "web, au rythme régulier : un essai d'identifiants par "
                  "requête.",
            "ar": "تدفقات POST متكررة متشابهة الحجم نحو منفذ الويب بإيقاع "
                  "منتظم: تخمين واحد لكل طلب.",
        },
        "checks": {
            "en": ["Check web/WAF logs for bursts of 401/403 responses per "
                   "source IP",
                   "Check whether the attempted usernames exist (credential "
                   "stuffing vs blind brute force)",
                   "Rule out SSO retry storms and misbehaving mobile "
                   "clients"],
            "fr": ["Vérifier les logs web/WAF : rafales de réponses 401/403 "
                   "par IP source",
                   "Vérifier si les identifiants essayés existent "
                   "(credential stuffing vs force brute aveugle)",
                   "Écarter les tempêtes de retry SSO et les clients mobiles "
                   "défaillants"],
            "ar": ["فحص سجلات الويب/WAF: دفعات استجابات 401/403 لكل مصدر",
                   "التحقق من وجود أسماء المستخدمين المجرَّبة (حشو بيانات أم "
                   "قوة غاشمة عمياء)",
                   "استبعاد عواصف إعادة محاولة SSO وعملاء الجوال المعطوبين"],
        },
        "fp_notes": {
            "en": "Authentication retry storms after a password change or "
                  "an SSO outage mimic this pattern.",
            "fr": "Les tempêtes de reconnexion après un changement de mot de "
                  "passe ou une panne SSO imitent ce motif.",
            "ar": "عواصف إعادة المصادقة بعد تغيير كلمة مرور أو عطل SSO تحاكي "
                  "هذا النمط.",
        },
    },
    "Web_AttackSql_Injection": {
        "fp_risk": "medium",
        "what": {
            "en": "SQL injection: crafted input in web parameters attempts "
                  "to manipulate the backend database (read, modify or dump "
                  "data).",
            "fr": "Injection SQL : des entrées forgées dans les paramètres "
                  "web tentent de manipuler la base de données (lecture, "
                  "modification ou extraction).",
            "ar": "حقن SQL: مدخلات مصمَّمة في معاملات الويب تحاول التلاعب "
                  "بقاعدة البيانات (قراءة أو تعديل أو تفريغ).",
        },
        "signals": {
            "en": "Slightly larger request payloads to the web port and "
                  "atypical response sizes (database errors or dumps) "
                  "compared with normal form traffic.",
            "fr": "Des charges de requête un peu plus grandes vers le port "
                  "web et des tailles de réponse atypiques (erreurs ou "
                  "extractions de base) par rapport au trafic de formulaire "
                  "normal.",
            "ar": "حمولات طلب أكبر قليلًا نحو منفذ الويب وأحجام استجابة شاذة "
                  "(أخطاء قاعدة بيانات أو تفريغ) مقارنة بحركة النماذج "
                  "العادية.",
        },
        "checks": {
            "en": ["Inspect web/WAF logs for SQL meta-characters (quotes, "
                   "UNION, comments) in the flagged requests",
                   "Check database logs for error spikes or unusual "
                   "queries at the same timestamps",
                   "Identify the targeted endpoint and whether it uses "
                   "parameterised queries"],
            "fr": ["Inspecter les logs web/WAF : méta-caractères SQL "
                   "(guillemets, UNION, commentaires) dans les requêtes "
                   "signalées",
                   "Vérifier les logs base de données : pics d'erreurs ou "
                   "requêtes inhabituelles aux mêmes horodatages",
                   "Identifier l'endpoint visé et s'il utilise des requêtes "
                   "paramétrées"],
            "ar": ["فحص سجلات الويب/WAF: محارف SQL (اقتباسات، UNION، "
                   "تعليقات) في الطلبات المبلَّغ عنها",
                   "فحص سجلات قاعدة البيانات: ذروات أخطاء أو استعلامات غير "
                   "معتادة بالتوقيت نفسه",
                   "تحديد نقطة النهاية المستهدفة وهل تستخدم استعلامات "
                   "مُعاملة"],
        },
        "fp_notes": {
            "en": "Applications that legitimately post SQL-like text "
                  "(forums, code paste, admin consoles) are the classic "
                  "benign trigger.",
            "fr": "Les applications qui envoient légitimement du texte "
                  "ressemblant à du SQL (forums, partage de code, consoles "
                  "d'administration) sont le déclencheur bénin classique.",
            "ar": "التطبيقات التي ترسل نصًا شبيهًا بـSQL بشكل مشروع "
                  "(منتديات، لصق أكواد، لوحات إدارة) هي المطلق الحميد "
                  "الكلاسيكي.",
        },
    },
    "Web_AttackXSS": {
        "fp_risk": "medium",
        "what": {
            "en": "Cross-site scripting (XSS): injection of script content "
                  "into web parameters, aiming to execute in other users' "
                  "browsers.",
            "fr": "Cross-site scripting (XSS) : injection de contenu script "
                  "dans les paramètres web, visant à s'exécuter dans le "
                  "navigateur d'autres utilisateurs.",
            "ar": "البرمجة العابرة للمواقع (XSS): حقن محتوى برمجي في معاملات "
                  "الويب بهدف التنفيذ في متصفحات مستخدمين آخرين.",
        },
        "signals": {
            "en": "Web-port requests whose payload sizes and reflection "
                  "patterns differ from normal form submissions.",
            "fr": "Des requêtes vers le port web dont les tailles de charge "
                  "et les motifs de réflexion diffèrent des envois de "
                  "formulaire normaux.",
            "ar": "طلبات نحو منفذ الويب تختلف أحجام حمولتها وأنماط انعكاسها "
                  "عن إرسال النماذج العادي.",
        },
        "checks": {
            "en": ["Inspect web/WAF logs for script tags or event handlers "
                   "in the flagged parameters",
                   "Check CSP violation reports around the same time",
                   "Determine whether the endpoint reflects user input "
                   "without encoding"],
            "fr": ["Inspecter les logs web/WAF : balises script ou "
                   "gestionnaires d'événements dans les paramètres signalés",
                   "Vérifier les rapports de violation CSP au même moment",
                   "Déterminer si l'endpoint réfléchit l'entrée utilisateur "
                   "sans encodage"],
            "ar": ["فحص سجلات الويب/WAF: وسوم script أو معالجات أحداث في "
                   "المعاملات المبلَّغ عنها",
                   "مراجعة تقارير انتهاك CSP في الوقت نفسه",
                   "تحديد ما إذا كانت نقطة النهاية تعكس مدخلات المستخدم دون "
                   "ترميز"],
        },
        "fp_notes": {
            "en": "Rich-text editors and users legitimately posting HTML "
                  "snippets are frequent benign triggers.",
            "fr": "Les éditeurs de texte riche et les utilisateurs postant "
                  "légitimement des extraits HTML sont des déclencheurs "
                  "bénins fréquents.",
            "ar": "محررات النص الغني والمستخدمون الذين ينشرون مقتطفات HTML "
                  "بشكل مشروع مطلقات حميدة شائعة.",
        },
    },
}

#: Entrée générique si une classe n'est pas répertoriée.
DEFAULT = {
    "fp_risk": "medium",
    "what": {
        "en": "Attack class flagged by the calibrated ensemble.",
        "fr": "Classe d'attaque signalée par l'ensemble calibré.",
        "ar": "فئة هجوم أبلغت عنها المجموعة المعايَرة.",
    },
    "signals": {
        "en": "The listed features deviated jointly from the benign "
              "profile learned in training.",
        "fr": "Les features listées ont dévié conjointement du profil bénin "
              "appris à l'entraînement.",
        "ar": "انحرفت الخصائص المذكورة مجتمعة عن النمط الحميد المتعلَّم "
              "أثناء التدريب.",
    },
    "checks": {
        "en": ["Corroborate with logs of the targeted service",
               "Check the source host's recent activity",
               "Assess the impact of the proposed remediation before "
               "approving"],
        "fr": ["Corroborer avec les logs du service visé",
               "Vérifier l'activité récente de l'hôte source",
               "Évaluer l'impact de la remédiation proposée avant "
               "d'approuver"],
        "ar": ["التثبت من سجلات الخدمة المستهدفة",
               "فحص النشاط الأخير للمضيف المصدر",
               "تقييم أثر الإجراء المقترح قبل الموافقة"],
    },
    "fp_notes": {
        "en": "No class-specific false-positive profile available.",
        "fr": "Pas de profil de faux positifs spécifique disponible pour "
              "cette classe.",
        "ar": "لا يتوفر ملف إنذارات كاذبة خاص بهذه الفئة.",
    },
}


def get_kb(predicted_class: str) -> dict:
    return KB.get(predicted_class, DEFAULT)


# ------------------------------------------------------------------ reco
#: Rationales localisées de la recommandation consultative (assemblées
#: selon la règle déterministe de `recommend`).
_RECO_TEXT = {
    "approve": {
        "en": "High fused confidence ({conf}%) with {agree} detector "
              "agreement, and this class has a {fp} false-positive "
              "propensity: the evidence supports approving the remediation. "
              "Run the checks below if time allows.",
        "fr": "Confiance fusionnée élevée ({conf} %) avec un accord de "
              "{agree} détecteurs, et cette classe a une propension {fp} "
              "aux faux positifs : les éléments soutiennent l'approbation "
              "de la remédiation. Déroulez les vérifications ci-dessous si "
              "le temps le permet.",
        "ar": "ثقة مدمجة عالية ({conf}٪) مع اتفاق {agree} من الكواشف، وهذه "
              "الفئة ذات ميل {fp} للإنذارات الكاذبة: الأدلة تدعم الموافقة "
              "على الإجراء. نفّذ الفحوصات أدناه إن سمح الوقت.",
    },
    "verify_first": {
        "en": "The verdict is plausible but {reason}: run the checks below "
              "before approving. If they corroborate the alert, approve; "
              "otherwise reject with a reason.",
        "fr": "Le verdict est plausible mais {reason} : déroulez les "
              "vérifications ci-dessous avant d'approuver. Si elles "
              "corroborent l'alerte, approuvez ; sinon rejetez en motivant.",
        "ar": "الحكم معقول لكن {reason}: نفّذ الفحوصات أدناه قبل الموافقة. "
              "إن أكدت التنبيه فوافق، وإلا فارفض مع ذكر السبب.",
    },
}

_REASONS = {
    "fp_class": {
        "en": "this class is prone to false positives",
        "fr": "cette classe est sujette aux faux positifs",
        "ar": "هذه الفئة معرضة للإنذارات الكاذبة",
    },
    "low_conf": {
        "en": "the fused confidence is moderate",
        "fr": "la confiance fusionnée est modérée",
        "ar": "الثقة المدمجة متوسطة",
    },
    "disagree": {
        "en": "the detectors disagree on the class",
        "fr": "les détecteurs ne sont pas unanimes sur la classe",
        "ar": "الكواشف غير متفقة على الفئة",
    },
}

_FP_WORD = {
    "low": {"en": "low", "fr": "faible", "ar": "منخفض"},
    "medium": {"en": "moderate", "fr": "modérée", "ar": "متوسط"},
    "high": {"en": "high", "fr": "forte", "ar": "مرتفع"},
}


def recommend(predicted_class: str, confidence: float,
              agreement: int, n_models: int) -> dict:
    """Recommandation consultative DÉTERMINISTE (jamais décisionnelle).

    Règle : approuver directement seulement si la confiance est haute,
    les détecteurs unanimes ET la classe peu sujette aux faux positifs ;
    sinon, vérifier d'abord (en citant pourquoi).
    """
    kb = get_kb(predicted_class)
    reasons = []
    if kb["fp_risk"] == "high":
        reasons.append("fp_class")
    if confidence < 0.90:
        reasons.append("low_conf")
    if agreement < n_models:
        reasons.append("disagree")

    verdict = "approve" if not reasons else "verify_first"
    rationale = {}
    for lang in ("en", "fr", "ar"):
        if verdict == "approve":
            rationale[lang] = _RECO_TEXT["approve"][lang].format(
                conf=round(100 * confidence),
                agree=f"{agreement}/{n_models}",
                fp=_FP_WORD[kb["fp_risk"]][lang])
        else:
            joiner = " ; " if lang != "ar" else "؛ "
            rationale[lang] = _RECO_TEXT["verify_first"][lang].format(
                reason=joiner.join(_REASONS[r][lang] for r in reasons))
    return {"verdict": verdict, "rationale": rationale,
            "fp_risk": kb["fp_risk"]}


def build_fallback(attribution: dict, agreement: int,
                   n_models: int) -> dict:
    """Aide à la décision sans LLM : socle de connaissances + features
    observées + recommandation déterministe. Entièrement localisée."""
    cls = attribution["predicted_class"]
    kb = get_kb(cls)
    top3 = ", ".join(t["name"] for t in attribution["top_features"][:3])
    interp = {}
    for lang in ("en", "fr", "ar"):
        lead = {
            "en": f"The strongest contributions come from {top3}. ",
            "fr": f"Les contributions les plus fortes viennent de {top3}. ",
            "ar": f"أقوى المساهمات جاءت من {top3}. ",
        }[lang]
        interp[lang] = (kb["what"][lang] + " " + kb["signals"][lang] + " "
                        + lead + kb["fp_notes"][lang])
    return {
        "attack_profile": kb["what"],
        "interpretation": interp,
        "checks": kb["checks"],
        "recommendation": recommend(
            cls, attribution["confidence"], agreement, n_models),
    }
