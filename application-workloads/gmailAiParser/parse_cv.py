#!/usr/bin/env python3
"""
Parse CV using Ollama AI to extract keywords and generate profile
"""
import sys
import io
import json
import requests
from pathlib import Path
import config

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def read_cv_file(file_path: str) -> str:
    """Read CV content from text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading CV file: {e}")
        sys.exit(1)

def parse_cv_with_ollama(cv_text: str) -> dict:
    """Use Ollama to parse CV and extract structured information"""

    model = config.OLLAMA_MODELS['job_extraction']

    prompt = f"""Analyze this CV and extract structured information in JSON format.

CV Content:
{cv_text}

Extract the following information and return ONLY valid JSON:
{{
  "name": "candidate name",
  "skills": ["list of technical skills, tools, methodologies"],
  "technologies": ["specific technologies, software, platforms"],
  "preferred_roles": ["job titles and roles they're suited for"],
  "domains": ["industry domains and areas of expertise"],
  "keywords": ["other relevant keywords"],
  "experience_level": "junior/mid/senior/lead",
  "locations": ["preferred work locations"],
  "contract_preferences": {{
    "type": "contract/permanent/both",
    "remote_preference": "remote/hybrid/onsite/flexible"
  }},
  "certifications": ["professional certifications"],
  "education": ["degrees and qualifications"]
}}

Focus on:
- SCCM, Intune, Autopilot, Windows deployment expertise
- Infrastructure and endpoint management skills
- Third line support capabilities
- Contract work preferences
- Location preferences (especially North East England)

Return ONLY the JSON object, no additional text."""

    print("🤖 Analyzing CV with Ollama (phi3:mini)...")
    print(f"   Model: {model}")
    print(f"   Ollama: {config.OLLAMA_BASE_URL}")
    print()

    try:
        response = requests.post(
            f"{config.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent output
                    "num_predict": 2000
                }
            },
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '').strip()

            # Try to extract JSON from response
            # Sometimes AI adds markdown code blocks
            if '```json' in ai_response:
                ai_response = ai_response.split('```json')[1].split('```')[0].strip()
            elif '```' in ai_response:
                ai_response = ai_response.split('```')[1].split('```')[0].strip()

            # Parse JSON
            try:
                parsed_data = json.loads(ai_response)
                return parsed_data
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON parsing error: {e}")
                print(f"AI Response:\n{ai_response[:500]}...")

                # Fallback: try to find JSON object in response
                import re
                json_match = re.search(r'\{[\s\S]*\}', ai_response)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group(0))
                        return parsed_data
                    except:
                        pass

                print("❌ Could not parse AI response as JSON")
                return None
        else:
            print(f"❌ Ollama request failed: {response.status_code}")
            return None

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Ollama at {config.OLLAMA_BASE_URL}")
        print("   Make sure Ollama is running (docker ps | grep ollama)")
        return None
    except Exception as e:
        print(f"❌ Error calling Ollama: {e}")
        return None

def enhance_profile_data(parsed_data: dict) -> dict:
    """Enhance parsed data with additional processing"""

    # Normalize all lists to lowercase
    if 'skills' in parsed_data:
        parsed_data['skills'] = [s.lower().strip() for s in parsed_data['skills']]

    if 'technologies' in parsed_data:
        parsed_data['technologies'] = [t.lower().strip() for t in parsed_data['technologies']]

    if 'preferred_roles' in parsed_data:
        parsed_data['preferred_roles'] = [r.lower().strip() for r in parsed_data['preferred_roles']]

    if 'keywords' in parsed_data:
        parsed_data['keywords'] = [k.lower().strip() for k in parsed_data['keywords']]

    if 'domains' in parsed_data:
        parsed_data['domains'] = [d.lower().strip() for d in parsed_data['domains']]

    # Add exclusions (jobs to avoid)
    parsed_data['exclusions'] = {
        "keywords": [
            "graduate", "junior", "internship", "apprentice",
            "entry level", "trainee"
        ],
        "locations": ["london", "south east", "abroad"],
        "contract_types": ["inside ir35", "zero hours"]
    }

    # Add description
    if 'name' in parsed_data:
        parsed_data['description'] = f"CV profile for {parsed_data['name']} - Automatically generated from CV analysis"

    return parsed_data

def save_profile(profile_data: dict, output_file: str):
    """Save profile to JSON file"""
    try:
        # Ensure profiles directory exists
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Profile saved to: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving profile: {e}")
        return False

def display_profile_summary(profile_data: dict):
    """Display summary of extracted profile"""
    print()
    print("=" * 60)
    print("Extracted CV Profile Summary")
    print("=" * 60)
    print()

    if 'name' in profile_data:
        print(f"👤 Name: {profile_data['name']}")
        print()

    if 'skills' in profile_data:
        print(f"🔧 Skills ({len(profile_data['skills'])}):")
        for skill in profile_data['skills'][:10]:
            print(f"   • {skill}")
        if len(profile_data['skills']) > 10:
            print(f"   ... and {len(profile_data['skills']) - 10} more")
        print()

    if 'technologies' in profile_data:
        print(f"💻 Technologies ({len(profile_data['technologies'])}):")
        for tech in profile_data['technologies'][:10]:
            print(f"   • {tech}")
        if len(profile_data['technologies']) > 10:
            print(f"   ... and {len(profile_data['technologies']) - 10} more")
        print()

    if 'preferred_roles' in profile_data:
        print(f"💼 Preferred Roles ({len(profile_data['preferred_roles'])}):")
        for role in profile_data['preferred_roles']:
            print(f"   • {role}")
        print()

    if 'experience_level' in profile_data:
        print(f"📊 Experience Level: {profile_data['experience_level']}")
        print()

    if 'locations' in profile_data:
        print(f"📍 Preferred Locations: {', '.join(profile_data['locations'])}")
        print()

    if 'certifications' in profile_data and profile_data['certifications']:
        print(f"🎓 Certifications: {', '.join(profile_data['certifications'])}")
        print()

def main():
    """Main function"""
    print("=" * 60)
    print("CV Parser - AI-Powered Profile Generation")
    print("=" * 60)
    print()

    # Check if CV file provided
    if len(sys.argv) < 2:
        print("Usage: py parse_cv.py <cv_file.txt>")
        print()
        print("Example:")
        print("  py parse_cv.py my_cv.txt")
        print()
        print("The CV should be in plain text format (.txt)")
        print("Copy your CV content into a text file first.")
        sys.exit(1)

    cv_file = sys.argv[1]

    if not Path(cv_file).exists():
        print(f"❌ CV file not found: {cv_file}")
        sys.exit(1)

    print(f"📄 Reading CV: {cv_file}")
    cv_text = read_cv_file(cv_file)
    print(f"   ✓ Read {len(cv_text)} characters")
    print()

    # Parse CV with AI
    parsed_data = parse_cv_with_ollama(cv_text)

    if not parsed_data:
        print("❌ Failed to parse CV with AI")
        sys.exit(1)

    print("✅ CV parsed successfully!")
    print()

    # Enhance the data
    profile_data = enhance_profile_data(parsed_data)

    # Display summary
    display_profile_summary(profile_data)

    # Save profile
    output_file = "profiles/graeme_suddick_profile.json"
    print("=" * 60)
    print(f"💾 Saving profile to: {output_file}")
    print("=" * 60)
    print()

    if save_profile(profile_data, output_file):
        print()
        print("=" * 60)
        print("✅ Profile Generation Complete!")
        print("=" * 60)
        print()
        print("Next Steps:")
        print("1. Review the generated profile:")
        print(f"   notepad {output_file}")
        print()
        print("2. Run job analysis with the new profile:")
        print("   py process_last_month.py")
        print()
        print("3. View results in web GUI:")
        print("   py web_gui.py")
        print()
    else:
        print("❌ Failed to save profile")
        sys.exit(1)

if __name__ == "__main__":
    main()
