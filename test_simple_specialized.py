#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import openai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def test_date_detection():
    """날짜 감지 테스트"""
    print("📅 날짜 감지 테스트")
    print("-" * 30)
    
    now = datetime.now()
    date_str = now.strftime("%Y년 %m월 %d일")
    
    if now.month in [12, 1, 2]:
        season = "겨울"
    elif now.month in [3, 4, 5]:
        season = "봄"
    elif now.month in [6, 7, 8]:
        season = "여름"
    else:
        season = "가을"
    
    print(f"✅ 현재 시점: {date_str}")
    print(f"   계절: {season}")
    
    return {"year": now.year, "month": now.month, "season": season, "date_str": date_str}

def test_ai_topics(date_info):
    """AI 주제 생성 테스트"""
    print(f"\n🤖 AI 주제 생성 테스트")
    print("-" * 25)
    
    if not openai.api_key:
        print("⚠️ OpenAI API 키 없음")
        return ["대체 주제 1", "대체 주제 2", "대체 주제 3"]
    
    try:
        prompt = f"""
현재: {date_info["date_str"]} ({date_info["season"]})

전문 분야 블로그 주제 5개를 만들어주세요:
분야: 기후변화, 재테크, IT, 주식, 경제

조건:
- 전문적이고 분석적인 내용
- {date_info["year"]}년 {date_info["month"]}월 시점성 반영

형식:
1. 주제명
2. 주제명
3. 주제명
4. 주제명
5. 주제명
"""
        
        print("🔄 AI 요청 중...")
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.6
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"📥 AI 응답: {len(ai_response)} 글자")
        
        topics = []
        for line in ai_response.split("\n"):
            line = line.strip()
            match = re.match(r"^\d+\.\s*(.+)", line)
            if match:
                topic = match.group(1).strip()
                if len(topic) > 8:
                    topics.append(topic)
        
        print(f"✅ 생성된 주제 ({len(topics)}개):")
        for i, topic in enumerate(topics, 1):
            print(f"   {i}. {topic}")
        
        return topics
        
    except Exception as e:
        print(f"❌ AI 생성 실패: {e}")
        return ["대체 주제 1", "대체 주제 2", "대체 주제 3"]

def main():
    print("🧪 간단한 전문 분야 테스트")
    print("=" * 40)
    
    try:
        date_info = test_date_detection()
        topics = test_ai_topics(date_info)
        
        print(f"\n🎉 테스트 완료!")
        print(f"✅ 총 {len(topics)}개 주제 생성")
        
    except Exception as e:
        print(f"❌ 오류: {e}")

if __name__ == "__main__":
    main() 