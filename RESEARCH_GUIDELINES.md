# Research Guidelines

## 1. Problem Statement
Describe the main challenge or opportunity this project addresses.  
Example: *Users struggle with offline access in productivity apps. Our goal is to provide seamless sync between offline and online states.*

## 2. Target Audience
Who will use this project?  
- Primary users:  
- Secondary users:  

## 3. Competitor / Market Research
List competing apps, tools, or libraries.  
- Competitor A: strengths / weaknesses  
- Competitor B: strengths / weaknesses  
- Market gap this project fills:  

## 4. Technical Constraints
Define requirements and limitations:  
- Must support **SDK 24+**  
- API requests limited to **100/minute**  
- No reliance on **proprietary services**  

## 5. Design Principles
Define the non-functional requirements:  
- Keep code modular and testable  
- Favor open standards (e.g., OAuth2 for auth)  
- Offline-first UX  

## 6. Research Tasks
Break down what the AI should investigate or plan for:  
- Evaluate libraries for push notifications  
- Investigate battery optimization tradeoffs  
- Research strategies for offline DB sync  

## 7. Success Metrics
How do we measure success?  
- App starts under **1s**  
- Sync conflicts resolved within **5s**  
- <2% crash rate in production  

## 8. References
Provide links or papers:  
- [Android Offline Sync Docs](https://developer.android.com/training/offline)  
- [Kotlin Coroutines Best Practices](https://kotlinlang.org/docs/coroutines-guide.html)  

