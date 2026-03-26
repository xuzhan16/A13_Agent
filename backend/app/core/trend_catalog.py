TREND_SNAPSHOT_VERSION = 'trend-snapshot/2026.03'
TREND_UPDATED_AT = '2026-03-20'


ROLE_TREND_CONFIG = {
    '\u004aava\u5f00\u53d1\u5de5\u7a0b\u5e08': {
        'growth_rate': 0.12,
        'tightness': 1.28,
        'demand_index': 84,
        'salary_index': 72,
        'summary': '\u004aava \u9700\u6c42\u4ecd\u4fdd\u6301\u7a33\u5b9a\u9ad8\u4f4d\uff0c\u6b63\u5728\u4ece\u4f20\u7edf\u4e1a\u52a1\u5f00\u53d1\u5411\u4e91\u539f\u751f\u4e0e AI \u5e94\u7528\u96c6\u6210\u6f14\u8fdb\u3002',
        'personalized_focus': ['Docker', 'Kubernetes', 'CI/CD', 'AI API\u96c6\u6210'],
        'industry_shifts': [
            {
                'topic': 'AI \u5e94\u7528\u96c6\u6210',
                'impact_level': 'high',
                'summary': '\u004aava \u540e\u7aef\u5c97\u4f4d\u5f00\u59cb\u8981\u6c42\u5177\u5907\u8c03\u7528\u5927\u6a21\u578b API\u3001\u6784\u5efa RAG \u670d\u52a1\u548c Agent \u5de5\u5177\u94fe\u7684\u80fd\u529b\u3002',
                'opportunities': ['AI \u5e94\u7528\u540e\u7aef', '\u4f01\u4e1a\u77e5\u8bc6\u5e93\u95ee\u7b54', '\u667a\u80fd\u4f53\u670d\u52a1\u7f16\u6392'],
                'risks': ['\u53ea\u4f1a\u4f20\u7edf CRUD \u7684\u5019\u9009\u4eba\u5dee\u5f02\u5316\u4e0d\u8db3'],
            },
            {
                'topic': '\u4e91\u539f\u751f\u5de5\u7a0b\u5316',
                'impact_level': 'high',
                'summary': '\u5bb9\u5668\u5316\u3001Kubernetes\u3001CI/CD \u548c\u53ef\u89c2\u6d4b\u6027\u6b63\u5728\u6210\u4e3a\u4e2d\u9ad8\u7ea7 Java \u5c97\u4f4d\u7684\u9ed8\u8ba4\u8981\u6c42\u3002',
                'opportunities': ['\u4e91\u539f\u751f\u540e\u7aef', '\u5e73\u53f0\u5de5\u7a0b', '\u9ad8\u53ef\u7528\u67b6\u6784'],
                'risks': ['\u7f3a\u5c11\u90e8\u7f72\u4e0e\u8fd0\u7ef4\u534f\u540c\u7ecf\u9a8c\u4f1a\u9650\u5236\u6210\u957f\u901f\u5ea6'],
            },
        ],
    },
    '\u524d\u7aef\u5f00\u53d1\u5de5\u7a0b\u5e08': {
        'growth_rate': 0.09,
        'tightness': 1.16,
        'demand_index': 76,
        'salary_index': 69,
        'summary': '\u524d\u7aef\u9700\u6c42\u7a33\u5b9a\uff0c\u4f46\u5c97\u4f4d\u91cd\u5fc3\u6b63\u4ece\u9875\u9762\u5b9e\u73b0\u8f6c\u5411\u7ec4\u4ef6\u5316\u3001\u4f53\u9a8c\u8bbe\u8ba1\u548c AI \u4ea4\u4e92\u3002',
        'personalized_focus': ['TypeScript', '\u5de5\u7a0b\u5316', '\u53ef\u89c6\u5316', 'AI UI'],
        'industry_shifts': [
            {
                'topic': '\u4f4e\u4ee3\u7801\u4e0e AIGC \u51b2\u51fb',
                'impact_level': 'high',
                'summary': '\u4f4e\u4ee3\u7801\u548c AI \u4ee3\u7801\u751f\u6210\u6b63\u5728\u66ff\u4ee3\u90e8\u5206\u57fa\u7840\u9875\u9762\u5f00\u53d1\uff0c\u524d\u7aef\u66f4\u5f3a\u8c03\u590d\u6742\u4ea4\u4e92\u548c\u4ea7\u54c1\u7406\u89e3\u3002',
                'opportunities': ['\u53ef\u89c6\u5316\u5e73\u53f0', '\u590d\u6742\u4ea4\u4e92\u7cfb\u7edf', 'AI \u4ea7\u54c1\u524d\u7aef'],
                'risks': ['\u53ea\u4f1a\u9759\u6001\u9875\u9762\u5b9e\u73b0\u7684\u5c97\u4f4d\u7ade\u4e89\u52a0\u5267'],
            },
        ],
    },
    '\u8f6f\u4ef6\u6d4b\u8bd5\u5de5\u7a0b\u5e08': {
        'growth_rate': 0.10,
        'tightness': 1.18,
        'demand_index': 73,
        'salary_index': 64,
        'summary': '\u6d4b\u8bd5\u5c97\u4f4d\u6b63\u4ece\u624b\u5de5\u9a8c\u8bc1\u5feb\u901f\u8f6c\u5411\u81ea\u52a8\u5316\u3001\u8d28\u91cf\u5e73\u53f0\u548c AI \u8f85\u52a9\u6d4b\u8bd5\u3002',
        'personalized_focus': ['Python', '\u81ea\u52a8\u5316\u6d4b\u8bd5', '\u6027\u80fd\u6d4b\u8bd5', 'CI/CD'],
        'industry_shifts': [
            {
                'topic': '\u4e91\u6d4b\u8bd5\u4e0e\u81ea\u52a8\u5316',
                'impact_level': 'high',
                'summary': '\u4e91\u539f\u751f\u67b6\u6784\u63a8\u52a8\u6d4b\u8bd5\u5de5\u7a0b\u5e08\u638c\u63e1\u63a5\u53e3\u81ea\u52a8\u5316\u3001\u6301\u7eed\u6d4b\u8bd5\u548c\u8d28\u91cf\u6d41\u6c34\u7ebf\u3002',
                'opportunities': ['\u6d4b\u8bd5\u5f00\u53d1', '\u8d28\u91cf\u5e73\u53f0\u5de5\u7a0b'],
                'risks': ['\u624b\u5de5\u6d4b\u8bd5\u7ecf\u9a8c\u96be\u4ee5\u652f\u6491\u957f\u671f\u7ade\u4e89\u529b'],
            },
        ],
    },
}


SKILL_TREND_CONFIG = {
    'Docker': {'growth_rate': 0.18, 'salary_premium': 0.08, 'demand_ratio': 0.62, 'transferability': 0.74, 'summary': '\u5bb9\u5668\u5316\u5df2\u7ecf\u662f\u5de5\u7a0b\u5316\u57fa\u7840\u80fd\u529b\u3002'},
    'Kubernetes': {'growth_rate': 0.31, 'salary_premium': 0.15, 'demand_ratio': 0.48, 'transferability': 0.68, 'summary': '\u4e91\u539f\u751f\u5c97\u4f4d\u7684\u5173\u952e\u95e8\u69db\u6280\u80fd\u3002'},
    'CI/CD': {'growth_rate': 0.14, 'salary_premium': 0.06, 'demand_ratio': 0.54, 'transferability': 0.72, 'summary': '\u6301\u7eed\u4ea4\u4ed8\u80fd\u529b\u6b63\u5728\u6210\u4e3a\u56e2\u961f\u9ed8\u8ba4\u8981\u6c42\u3002'},
    'AI API\u96c6\u6210': {'growth_rate': 0.52, 'salary_premium': 0.18, 'demand_ratio': 0.37, 'transferability': 0.66, 'summary': 'AI \u5e94\u7528\u63a5\u5165\u80fd\u529b\u662f\u672a\u6765 3 \u5e74\u7684\u91cd\u8981\u589e\u91cf\u7ade\u4e89\u529b\u3002'},
    'Python': {'growth_rate': 0.17, 'salary_premium': 0.07, 'demand_ratio': 0.58, 'transferability': 0.79, 'summary': 'Python \u5728\u6d4b\u8bd5\u81ea\u52a8\u5316\u3001\u6570\u636e\u5904\u7406\u548c AI \u573a\u666f\u4e2d\u4ecd\u6709\u8f83\u5f3a\u901a\u7528\u6027\u3002'},
    '\u81ea\u52a8\u5316\u6d4b\u8bd5': {'growth_rate': 0.20, 'salary_premium': 0.09, 'demand_ratio': 0.52, 'transferability': 0.64, 'summary': '\u81ea\u52a8\u5316\u6d4b\u8bd5\u662f\u6d4b\u8bd5\u5c97\u4f4d\u5347\u7ea7\u7684\u6838\u5fc3\u65b9\u5411\u3002'},
    '\u6027\u80fd\u6d4b\u8bd5': {'growth_rate': 0.13, 'salary_premium': 0.08, 'demand_ratio': 0.34, 'transferability': 0.41, 'summary': '\u6027\u80fd\u6d4b\u8bd5\u5728\u9ad8\u5e76\u53d1\u548c\u4e91\u670d\u52a1\u573a\u666f\u4e0b\u6709\u7a33\u5b9a\u6ea2\u4ef7\u3002'},
    'Linux': {'growth_rate': 0.10, 'salary_premium': 0.04, 'demand_ratio': 0.60, 'transferability': 0.82, 'summary': 'Linux \u4ecd\u7136\u662f\u5f00\u53d1\u3001\u6d4b\u8bd5\u3001\u8fd0\u7ef4\u534f\u540c\u7684\u57fa\u7840\u80fd\u529b\u3002'},
    'Redis': {'growth_rate': 0.09, 'salary_premium': 0.05, 'demand_ratio': 0.45, 'transferability': 0.51, 'summary': 'Redis \u5728\u9ad8\u6027\u80fd\u540e\u7aef\u573a\u666f\u4e2d\u4f9d\u65e7\u5e38\u89c1\u3002'},
    '\u6d88\u606f\u961f\u5217': {'growth_rate': 0.16, 'salary_premium': 0.10, 'demand_ratio': 0.39, 'transferability': 0.47, 'summary': '\u5206\u5e03\u5f0f\u7cfb\u7edf\u548c\u5f02\u6b65\u67b6\u6784\u5e26\u6765\u7a33\u5b9a\u9700\u6c42\u3002'},
}


GENERIC_INDUSTRY_SHIFTS = [
    {
        'topic': 'AI \u8f85\u52a9\u5de5\u4f5c\u6d41',
        'impact_level': 'medium',
        'summary': '\u8d8a\u6765\u8d8a\u591a\u5c97\u4f4d\u5f00\u59cb\u8981\u6c42\u5019\u9009\u4eba\u5177\u5907\u4f7f\u7528 AI \u63d0\u5347\u6548\u7387\u3001\u63a5\u5165 AI \u80fd\u529b\u6216\u7406\u89e3\u667a\u80fd\u4f53\u6d41\u7a0b\u7684\u80fd\u529b\u3002',
        'opportunities': ['AI \u5de5\u5177\u63d0\u6548', '\u667a\u80fd\u5de5\u4f5c\u6d41\u8bbe\u8ba1'],
        'risks': ['\u53ea\u5177\u5907\u4f20\u7edf\u5de5\u5177\u94fe\u7ecf\u9a8c\u4f1a\u524a\u5f31\u7ade\u4e89\u529b'],
    },
    {
        'topic': '\u5de5\u7a0b\u5316\u4e0e\u534f\u4f5c\u5347\u7ea7',
        'impact_level': 'medium',
        'summary': '\u4f01\u4e1a\u8d8a\u6765\u8d8a\u5173\u6ce8\u53ef\u4ea4\u4ed8\u3001\u53ef\u7ef4\u62a4\u548c\u8de8\u56e2\u961f\u534f\u4f5c\u7684\u7efc\u5408\u80fd\u529b\uff0c\u800c\u4e0d\u53ea\u662f\u5355\u70b9\u6280\u80fd\u3002',
        'opportunities': ['\u5de5\u7a0b\u5316\u5b9e\u8df5', '\u8de8\u5c97\u4f4d\u534f\u4f5c'],
        'risks': ['\u53ea\u4f1a\u5355\u70b9\u5b9e\u73b0\u800c\u7f3a\u5c11\u5de5\u7a0b\u610f\u8bc6\u4f1a\u5f71\u54cd\u6210\u957f\u901f\u5ea6'],
    },
]
