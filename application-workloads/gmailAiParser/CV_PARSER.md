# CV Parser - AI-Powered Profile Generation

Use Ollama AI to automatically parse your CV and generate an accurate keyword profile for job matching.

## Quick Start

### 1. Prepare Your CV

Convert your CV to plain text format:

```powershell
# Option A: Copy from Word/PDF and paste into a text file
notepad my_cv.txt

# Option B: If you have a .docx file, you can extract text
# (Manual: Open in Word, Save As > Plain Text)
```

**Tips for best results:**
- Include full job descriptions and responsibilities
- List all technical skills and tools
- Mention certifications and qualifications
- Include location preferences if stated
- Keep formatting simple (no fancy tables)

### 2. Run the CV Parser

```powershell
cd C:\users\gls\Documents\gmailAiParser
py parse_cv.py my_cv.txt
```

### 3. Review Generated Profile

The script will:
- ✅ Use Ollama (phi3:mini) to analyze your CV
- ✅ Extract skills, technologies, roles, and keywords
- ✅ Generate `profiles/graeme_suddick_profile.json`
- ✅ Show a summary of extracted information

## What It Extracts

The AI parser identifies:

### Technical Information
- **Skills**: SCCM, Intune, Autopilot, PowerShell, etc.
- **Technologies**: Microsoft Endpoint Manager, Windows 11, Active Directory, etc.
- **Domains**: Endpoint management, infrastructure, deployment, etc.
- **Certifications**: Microsoft certifications, qualifications

### Role Preferences
- **Preferred Roles**: Windows Engineer, Deployment Engineer, Third Line, etc.
- **Experience Level**: Junior/Mid/Senior/Lead
- **Contract Preferences**: Contract type, IR35, day rates

### Location Preferences
- **Locations**: Remote, Durham, Newcastle, North East, Hybrid, etc.
- **Exclusions**: Areas to avoid

## Example Output

```
📄 Reading CV: graeme_cv.txt
   ✓ Read 5432 characters

🤖 Analyzing CV with Ollama (phi3:mini)...
   Model: phi3:mini
   Ollama: http://localhost:11434

✅ CV parsed successfully!

============================================================
Extracted CV Profile Summary
============================================================

👤 Name: Graeme Suddick - Windows/SCCM/Intune Specialist

🔧 Skills (29):
   • sccm
   • intune
   • autopilot
   • windows 11
   • windows 10
   • powershell
   • active directory
   • group policy
   • endpoint management
   • deployment
   ... and 19 more

💻 Technologies (22):
   • microsoft endpoint manager
   • sccm
   • intune
   • autopilot
   • windows deployment services
   ... and 17 more

💼 Preferred Roles (21):
   • windows engineer
   • deployment engineer
   • third line engineer
   • endpoint engineer
   • sccm engineer
   ... and 16 more

📊 Experience Level: senior

📍 Preferred Locations: remote, durham, newcastle, north east, hybrid

🎓 Certifications: Microsoft Certified: Modern Desktop Administrator

============================================================
💾 Saving profile to: profiles/graeme_suddick_profile.json
============================================================

✅ Profile saved to: profiles/graeme_suddick_profile.json

============================================================
✅ Profile Generation Complete!
============================================================
```

## Advantages Over Manual Profiles

### AI Parsing Benefits
✅ **Comprehensive**: Captures nuances AI understands from context
✅ **Fast**: Generates profile in ~30 seconds
✅ **Accurate**: AI understands technical terminology and relationships
✅ **Consistent**: Standardized format every time
✅ **Easy Updates**: Rerun when CV changes

### Manual Profile Limitations
❌ Time-consuming to list every keyword
❌ Easy to forget relevant skills
❌ Hard to maintain consistency
❌ Tedious to update

## Customizing the Generated Profile

After generation, you can manually edit the JSON to:

1. **Add specific keywords**: Industry jargon, company names
2. **Adjust priorities**: Reorder skills by importance
3. **Set exclusions**: Add unwanted keywords/locations
4. **Fine-tune contract preferences**: Rates, IR35, duration

```powershell
# Edit the generated profile
notepad profiles\graeme_suddick_profile.json
```

## Regenerating Profile

If your CV changes:

```powershell
# Update your CV text file
notepad my_cv.txt

# Regenerate profile (overwrites existing)
py parse_cv.py my_cv.txt

# Run new analysis
py process_last_month.py
```

## Troubleshooting

### "Cannot connect to Ollama"
Ensure Ollama Docker is running:
```powershell
docker ps | Select-String ollama
```

If not running:
```powershell
docker start ollama
```

### "Could not parse AI response as JSON"
The AI sometimes generates invalid JSON. Try:
1. Simplify your CV text (remove special characters)
2. Run again (AI responses vary)
3. Check the displayed AI response for clues
4. Manually edit the generated JSON

### CV File Not Found
Ensure you provide the correct path:
```powershell
# Absolute path
py parse_cv.py C:\Users\gls\Documents\my_cv.txt

# Relative path
py parse_cv.py ..\my_cv.txt
```

### Poor Extraction Quality
For best results:
- Use plain text format (.txt)
- Include complete sentences
- List skills explicitly
- Avoid excessive formatting
- Keep tables simple

## Advanced Usage

### Parse Multiple CVs

```powershell
# Parse different versions for different roles
py parse_cv.py cv_windows_engineer.txt
Move-Item profiles\graeme_suddick_profile.json profiles\windows_engineer_profile.json

py parse_cv.py cv_deployment_specialist.txt
Move-Item profiles\graeme_suddick_profile.json profiles\deployment_profile.json
```

### Merge Profiles

You can manually merge multiple profiles to create a comprehensive master profile with all your skills.

### Version Control

```powershell
# Backup current profile
Copy-Item profiles\graeme_suddick_profile.json profiles\backup_profile.json

# Regenerate from updated CV
py parse_cv.py updated_cv.txt
```

## Integration

The generated profile works seamlessly with:

- **process_last_month.py**: Scores jobs against your profile
- **web_gui.py**: Displays job matches in the GUI
- **search_euc_jobs.py**: Generates Gmail search queries
- **job_detector.py**: Relevance scoring engine

## Technical Details

### AI Model
- Uses: `phi3:mini` (configured in config.py)
- Temperature: 0.3 (lower = more consistent)
- Max tokens: 2000
- Timeout: 120 seconds

### JSON Schema
```json
{
  "name": "string",
  "skills": ["array of strings"],
  "technologies": ["array of strings"],
  "preferred_roles": ["array of strings"],
  "domains": ["array of strings"],
  "keywords": ["array of strings"],
  "experience_level": "junior|mid|senior|lead",
  "locations": ["array of strings"],
  "contract_preferences": {
    "type": "contract|permanent|both",
    "remote_preference": "remote|hybrid|onsite|flexible",
    "min_day_rate": number,
    "max_day_rate": number,
    "ir35_preference": "outside|inside|either"
  },
  "certifications": ["array of strings"],
  "education": ["array of strings"],
  "exclusions": {
    "keywords": ["array of strings"],
    "locations": ["array of strings"],
    "contract_types": ["array of strings"]
  }
}
```

## Best Practices

1. **Keep CV Current**: Update text file when CV changes
2. **Regenerate Regularly**: Monthly or after major changes
3. **Review Output**: Always check AI extracted data
4. **Fine-tune Manually**: Add specific keywords AI might miss
5. **Test Results**: Run `process_last_month.py` after changes
6. **Backup Profiles**: Keep copies before regenerating
