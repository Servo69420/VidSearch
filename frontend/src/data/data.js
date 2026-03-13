export const TOPICS = [
  { label: 'CS Fundamentals', count: 12, color: 'chip-navy' },
  { label: 'Biology',          count: 8,  color: 'chip-teal' },
  { label: 'Mathematics',      count: 15, color: 'chip-gold' },
  { label: 'History',          count: 6,  color: 'chip-rose' },
  { label: 'Physics',          count: 9,  color: 'chip-sky' },
  { label: 'Machine Learning', count: 11, color: 'chip-violet' },
]

export const HOBBY_COLORS = {
  'CS Fundamentals': { chip: 'chip-navy',   thumb: 'thumb-navy' },
  'Biology':          { chip: 'chip-teal',   thumb: 'thumb-teal' },
  'Mathematics':      { chip: 'chip-gold',   thumb: 'thumb-gold' },
  'History':          { chip: 'chip-rose',   thumb: 'thumb-rose' },
  'Physics':          { chip: 'chip-sky',    thumb: 'thumb-sky' },
  'Machine Learning': { chip: 'chip-violet', thumb: 'thumb-violet' },
}

export const ALL_VIDEOS = [
  { id: 1,  title: 'How recursion works in Python',   subject: 'CS Fundamentals', duration: '4:12',  color: 'thumb-navy',   icon: '\u27F3', youtubeId: 'ivl5-snqul8', description: 'A deep dive into recursion concepts, base cases, and recursive thinking in Python programming.' },
  { id: 2,  title: 'Data structures overview',        subject: 'CS Fundamentals', duration: '6:45',  color: 'thumb-navy',   icon: '\u229E', youtubeId: 'bum_19loj9A', description: 'Comprehensive overview of fundamental data structures including arrays, linked lists, trees, and graphs.' },
  { id: 3,  title: 'Object-oriented programming',     subject: 'CS Fundamentals', duration: '7:20',  color: 'thumb-navy',   icon: '\u25FB', youtubeId: 'pTB0EiLXUC8', description: 'Learn the four pillars of OOP: encapsulation, inheritance, polymorphism, and abstraction.' },
  { id: 4,  title: 'What is photosynthesis?',         subject: 'Biology',         duration: '3:28',  color: 'thumb-teal',   icon: '\uD83C\uDF3F', youtubeId: 'sQK3Yr4Sc_k', description: 'Understanding how plants convert sunlight into energy through the process of photosynthesis.' },
  { id: 5,  title: 'How DNA replication works',       subject: 'Biology',         duration: '5:10',  color: 'thumb-teal',   icon: '\u25CE', youtubeId: 'TNKWgcFPHqw', description: 'Step-by-step explanation of DNA replication, from helicase unwinding to polymerase synthesis.' },
  { id: 6,  title: 'Cell division explained',         subject: 'Biology',         duration: '4:45',  color: 'thumb-teal',   icon: '\u2295', youtubeId: 'SEejG35IWlE', description: 'Mitosis and meiosis explained with clear visuals and real-world examples.' },
  { id: 7,  title: 'Introduction to calculus',        subject: 'Mathematics',     duration: '9:15',  color: 'thumb-gold',   icon: '\u222B', youtubeId: 'WUvTyaaNkzM', description: 'Your first steps into calculus: limits, derivatives, and the fundamental theorem.' },
  { id: 8,  title: 'Linear algebra basics',           subject: 'Mathematics',     duration: '8:30',  color: 'thumb-gold',   icon: '\u2211', youtubeId: 'fNk_zzaMoSs', description: 'Vectors, matrices, and linear transformations explained visually and intuitively.' },
  { id: 9,  title: 'Statistics fundamentals',         subject: 'Mathematics',     duration: '6:55',  color: 'thumb-gold',   icon: '\u221E', youtubeId: 'xxpc-HPKN28', description: 'Mean, median, standard deviation, and probability distributions made simple.' },
  { id: 10, title: 'The French Revolution explained', subject: 'History',         duration: '8:01',  color: 'thumb-rose',   icon: '\u2691', youtubeId: '8qRZcXIODNU', description: 'From the storming of the Bastille to the rise of Napoleon: a complete overview.' },
  { id: 11, title: 'The rise of the Roman Empire',    subject: 'History',         duration: '11:20', color: 'thumb-rose',   icon: '\u2694', youtubeId: 'oPf27gAup9U', description: 'How Rome grew from a small city-state to the greatest empire of the ancient world.' },
  { id: 12, title: "Newton's laws of motion",         subject: 'Physics',         duration: '6:30',  color: 'thumb-sky',    icon: '\u229B', youtubeId: 'kKKM8Y-u7ds', description: 'The three laws that govern all motion, explained with everyday examples.' },
  { id: 13, title: 'Quantum mechanics intro',         subject: 'Physics',         duration: '10:05', color: 'thumb-sky',    icon: '\u2B21', youtubeId: 'p7bzE1E5PMY', description: 'Wave-particle duality, superposition, and the uncertainty principle demystified.' },
  { id: 14, title: 'Thermodynamics explained',        subject: 'Physics',         duration: '7:15',  color: 'thumb-sky',    icon: '\u25C8', youtubeId: 'brpPjQ_5lNI', description: 'The laws of thermodynamics and how energy flows through systems.' },
  { id: 15, title: 'Intro to neural networks',        subject: 'Machine Learning',duration: '5:55',  color: 'thumb-violet', icon: '\u25C9', youtubeId: 'aircAruvnKk', description: 'How artificial neural networks learn patterns from data, layer by layer.' },
  { id: 16, title: 'Decision trees explained',        subject: 'Machine Learning',duration: '7:40',  color: 'thumb-violet', icon: '\u22A2', youtubeId: '_L39rN6gz7Y', description: 'Classification and regression trees: how they split data to make predictions.' },
  { id: 17, title: 'Natural language processing',     subject: 'Machine Learning',duration: '9:25',  color: 'thumb-violet', icon: '\u2297', youtubeId: 'fOvTtapxa9c', description: 'From tokenization to transformers: how machines understand human language.' },
]

export const PRICING_PLANS = [
  {
    name: 'Free',
    price: 0,
    period: 'forever',
    description: 'Get started with basic video explanations',
    features: [
      '5 video explanations per month',
      'Basic Q&A with AI assistant',
      'Search & browse video library',
      'Community support',
    ],
    cta: 'Get Started',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: 12,
    period: 'month',
    description: 'For serious learners who want more',
    features: [
      'Unlimited video explanations',
      'Advanced Q&A with context memory',
      'Save clips & bookmarks',
      'Search history & analytics',
      'Priority support',
      'Export notes as PDF',
    ],
    cta: 'Start Free Trial',
    highlighted: true,
  },
  {
    name: 'Premium',
    price: 29,
    period: 'month',
    description: 'For teams and power users',
    features: [
      'Everything in Pro',
      'Team collaboration workspace',
      'Custom AI model fine-tuning',
      'API access',
      'Dedicated account manager',
      'SSO & advanced security',
      'Custom integrations',
    ],
    cta: 'Contact Sales',
    highlighted: false,
  },
]

export const FAQ_ITEMS = [
  { question: 'What is VideoSearch?', answer: 'VideoSearch is an AI-powered video learning platform that helps you understand any YouTube video through interactive Q&A. Paste a video link, and our AI will analyze the content so you can ask questions, get explanations, and save key insights.' },
  { question: 'How does the AI explanation work?', answer: 'Our AI processes the video transcript and visual content to build a deep understanding of the material. You can then ask questions in natural language, and the AI provides accurate, context-aware answers referencing specific parts of the video.' },
  { question: 'Is there a free plan?', answer: 'Yes! Our Free plan gives you 5 video explanations per month with basic Q&A capabilities. No credit card required to get started.' },
  { question: 'Can I cancel my subscription anytime?', answer: 'Absolutely. You can cancel your Pro or Premium subscription at any time from your account settings. You will retain access until the end of your current billing period.' },
  { question: 'What types of videos are supported?', answer: 'VideoSearch works with any public YouTube video. Whether it is a lecture, tutorial, documentary, or educational content, our AI can process and explain it.' },
  { question: 'How do saved clips work?', answer: 'While watching a video, you can bookmark specific timestamps and add notes. These saved clips are organized in your library for easy review and can be exported or shared.' },
  { question: 'Is my data secure?', answer: 'Yes. We use industry-standard encryption for all data in transit and at rest. We never share your personal information or viewing history with third parties.' },
  { question: 'Do you offer refunds?', answer: 'We offer a full refund within the first 7 days of any paid subscription. After that, you can cancel at any time but refunds are not available for partial billing periods.' },
]

export const FEATURES = [
  { title: 'AI-Powered Q&A', description: 'Ask any question about a video and get instant, accurate answers powered by advanced AI.', icon: '\uD83E\uDDE0' },
  { title: 'Smart Timestamps', description: 'Jump to the exact moment in a video that answers your question. No more scrubbing.', icon: '\u23F1\uFE0F' },
  { title: 'Save & Organize', description: 'Bookmark key moments, add notes, and build your personal knowledge library.', icon: '\uD83D\uDCDA' },
  { title: 'Learn Any Subject', description: 'From CS to biology, math to history. Works with any educational YouTube video.', icon: '\uD83C\uDF93' },
  { title: 'Track Progress', description: 'See your learning stats, streak, and topics covered at a glance on your dashboard.', icon: '\uD83D\uDCC8' },
  { title: 'Works Instantly', description: 'Just paste a YouTube URL and start asking questions. No setup, no downloads.', icon: '\u26A1' },
]

export const HOW_IT_WORKS_STEPS = [
  { step: 1, title: 'Paste a Video Link', description: 'Copy any YouTube video URL and paste it into the VideoSearch workspace. Our AI begins processing the video immediately.' },
  { step: 2, title: 'Ask Questions', description: 'Type any question about the video content. The AI understands context, nuance, and can reference specific timestamps.' },
  { step: 3, title: 'Get Instant Answers', description: 'Receive detailed, accurate explanations with references to the exact moments in the video. Save insights for later.' },
  { step: 4, title: 'Build Your Knowledge', description: 'Track your progress, revisit saved clips, and build a personal library of video-based learning materials.' },
]

export const TESTIMONIALS = [
  { name: 'Sarah Chen', role: 'Computer Science Student', quote: 'VideoSearch completely changed how I study. I can watch a lecture and instantly get clarification on anything I missed.', avatar: 'SC' },
  { name: 'James Rodriguez', role: 'High School Teacher', quote: 'I use VideoSearch to prepare lesson materials. The AI explanations help me find the best teaching moments in educational videos.', avatar: 'JR' },
  { name: 'Emily Park', role: 'Self-Learner', quote: 'As someone who learns best from videos, this tool is a game-changer. The saved clips feature is incredibly useful for review.', avatar: 'EP' },
]

export const SAMPLE_HISTORY = [
  { id: 1, query: 'How does recursion work?', timestamp: '2 hours ago', videoTitle: 'How recursion works in Python' },
  { id: 2, query: 'What is the base case?', timestamp: '2 hours ago', videoTitle: 'How recursion works in Python' },
  { id: 3, query: 'Explain photosynthesis steps', timestamp: 'Yesterday', videoTitle: 'What is photosynthesis?' },
  { id: 4, query: 'What are the products of light reactions?', timestamp: 'Yesterday', videoTitle: 'What is photosynthesis?' },
  { id: 5, query: 'Difference between mitosis and meiosis', timestamp: '3 days ago', videoTitle: 'Cell division explained' },
  { id: 6, query: 'What is a derivative?', timestamp: '1 week ago', videoTitle: 'Introduction to calculus' },
  { id: 7, query: 'How do neural networks learn?', timestamp: '1 week ago', videoTitle: 'Intro to neural networks' },
  { id: 8, query: 'What is backpropagation?', timestamp: '2 weeks ago', videoTitle: 'Intro to neural networks' },
]

export const SAMPLE_WATCHED = [
  { videoId: 1, watchedAt: '2 hours ago', progress: 100 },
  { videoId: 4, watchedAt: 'Yesterday', progress: 75 },
  { videoId: 6, watchedAt: 'Yesterday', progress: 100 },
  { videoId: 7, watchedAt: '3 days ago', progress: 60 },
  { videoId: 15, watchedAt: '1 week ago', progress: 100 },
  { videoId: 12, watchedAt: '1 week ago', progress: 45 },
  { videoId: 8, watchedAt: '2 weeks ago', progress: 100 },
  { videoId: 10, watchedAt: '2 weeks ago', progress: 90 },
]

export const SAMPLE_SAVED = [
  { id: 1, videoId: 1, timestamp: '2:34', note: 'Great explanation of the call stack', savedAt: '2 hours ago' },
  { id: 2, videoId: 7, timestamp: '5:12', note: 'Intuitive way to think about limits', savedAt: '3 days ago' },
  { id: 3, videoId: 15, timestamp: '3:45', note: 'How weights are adjusted during training', savedAt: '1 week ago' },
  { id: 4, videoId: 4, timestamp: '1:20', note: 'Light-dependent vs light-independent reactions', savedAt: '1 week ago' },
  { id: 5, videoId: 13, timestamp: '7:30', note: 'Schrodinger equation simplified', savedAt: '2 weeks ago' },
]

export const SAMPLE_NOTIFICATIONS = [
  { id: 1, type: 'info', title: 'New video added', message: 'A new Machine Learning video has been added to the library.', time: '1 hour ago', read: false },
  { id: 2, type: 'success', title: 'Streak milestone', message: 'Congratulations! You have maintained a 7-day learning streak.', time: '3 hours ago', read: false },
  { id: 3, type: 'info', title: 'Feature update', message: 'You can now export your saved clips as PDF notes.', time: '1 day ago', read: true },
  { id: 4, type: 'warning', title: 'Subscription reminder', message: 'Your Pro trial ends in 3 days. Upgrade to keep unlimited access.', time: '2 days ago', read: true },
  { id: 5, type: 'success', title: 'Bookmark synced', message: 'Your 5 saved clips have been synced across devices.', time: '3 days ago', read: true },
]

export const SAMPLE_USER_STATS = {
  videosExplained: 24,
  topicsCovered: 6,
  watchLater: 11,
  streak: 7,
  totalQuestions: 147,
  avgSessionTime: '18 min',
}
