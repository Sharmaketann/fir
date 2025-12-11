import re
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class FIRExtractionService:
    def __init__(self):
        """Initialize extraction patterns for FIR fields"""
        self.patterns = {
            'fir_no': r'FIR\s*No\.\s*:\s*(\d{4})',
            'date_time': r'Date\s*and\s*Time\s*of\s*FIR.*?:.*?(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})',
            'district': r'District.*?:\s*(.*?)(?:\s*Year|\s*$)',
            'police_station': r'P\.S\..*?:\s*(.*?)(?:\s*Year|\s*$)',
            'year': r'Year.*?:\s*(\d{4})',
            'mobile': r'(?:मोब\.?नं\.?|Mobile|Phone).*?(\d{10})',
            'complainant_name': r'(?:Complainant|फिर्यादी|Informant).*?(?:Name|नाव).*?:(.*?)(?:Father|वडील|$)',
            'father_name': r'(?:Father|वडील).*?(?:Name|नाव).*?:(.*?)(?:DOB|वय|$)',
            'dob': r'(?:DOB|Date.*Birth|वय).*?(\d{4})',
            'address': r'(?:Address|पत्ता).*?:(.*?)(?:Phone|Mobile|$)',
            'acts_sections': r'(?:भारतीय न्याय संहिता|Indian Penal Code|BNS).*?(\d+)',
            'day': r'Day.*?:\s*(.*?)(?:\s*Date|$)',
            'time_period': r'Time\s*Period.*?:\s*(.*?)(?:\s*Time|$)',
            'direction': r'Direction.*?:\s*(.*?)(?:\s*Distance|$)',
            'distance': r'Distance.*?:\s*(.*?)(?:\s*Beat|$)',
            'officer_name': r'(?:Officer|अधिकारी).*?(?:Name|नाव).*?:(.*?)(?:Rank|पद|$)',
            'rank': r'Rank.*?:\s*(.*?)(?:\s*No|$)',
            'officer_no': r'No\.\s*:\s*(.*?)(?:\s*$)',
        }

        # Load improved patterns if available
        self._load_improved_patterns()
    
    def extract_fields(self, ocr_data: List[Dict]) -> Dict[str, Any]:
        """Extract structured fields from OCR data"""
        # Filter out low-confidence OCR text and clean it
        filtered_ocr = [item for item in ocr_data if item.get('confidence', 0) > 0.3]
        cleaned_ocr = self._clean_ocr_text(filtered_ocr)

        # Combine all cleaned text
        full_text = ' '.join([item['text'] for item in cleaned_ocr])

        extracted_fields = {
            'FIR': {
                'District': '',
                'PoliceStation': '',
                'Year': 0,
                'FIRNo': '',
                'DateTimeOfFIR': '',
                'ActsSections': [],
                'OccurrenceOfOffence': {
                    'Day': '',
                    'DateFrom': '',
                    'DateTo': '',
                    'TimePeriod': '',
                    'TimeFrom': '',
                    'TimeTo': ''
                },
                'InfoReceivedAtPS': {
                    'Date': '',
                    'Time': ''
                },
                'GeneralDiaryReference': {
                    'EntryNo': '',
                    'DateTime': ''
                },
                'TypeOfInformation': '',
                'PlaceOfOccurrence': {
                    'DirectionDistanceFromPS': {
                        'Direction': '',
                        'Distance': ''
                    },
                    'BeatNo': '',
                    'Address': '',
                    'DistrictState': ''
                }
            },
            'ComplainantInformant': {
                'Name': '',
                'FatherOrHusbandName': '',
                'DOB_YearOfBirth': '',
                'Nationality': 'भारत',
                'UIDNo': '',
                'PassportNo': '',
                'IDDetails': [],
                'Occupation': '',
                'Addresses': [],
                'PhoneNumber': ''
            },
            'AccusedDetails': [],
            'PropertyOfInterest': [],
            'TotalValueOfPropertyInRs': '',
            'Inquest_UDB_CaseNo': [],
            'FirstInformationContents': '',
            'ActionTaken': {
                'RegisteredCaseInvestigation': {
                    'OfficerName': '',
                    'Rank': '',
                    'No': ''
                },
                'DirectedNameOfIO': '',
                'DirectedRank': '',
                'DirectedNo': '',
                'RefusedInvestigationDueTo': '',
                'TransferredPS': '',
                'TransferredDistrict': '',
                'ROAC': ''
            },
            'ComplainantSignature': {
                'Name': '',
                'Rank': '',
                'No': ''
            },
            'DateTimeOfDispatchToCourt': '',
            'AccusedPhysicalDetails': []
        }

        try:
            # Extract FIR basic info
            extracted_fields['FIR'].update(self._extract_fir_info(cleaned_ocr, full_text))

            # Extract complainant details
            extracted_fields['ComplainantInformant'].update(self._extract_complainant(cleaned_ocr, full_text))

            # Extract accused details
            extracted_fields['AccusedDetails'] = self._extract_accused(cleaned_ocr)

            # Extract occurrence details
            extracted_fields['FIR']['OccurrenceOfOffence'] = self._extract_occurrence(cleaned_ocr, full_text)

            # Extract acts and sections
            extracted_fields['FIR']['ActsSections'] = self._extract_acts_sections(cleaned_ocr, full_text)

            # Extract place of occurrence
            extracted_fields['FIR']['PlaceOfOccurrence'] = self._extract_place(cleaned_ocr, full_text)

            # Extract action taken
            extracted_fields['ActionTaken'] = self._extract_action_taken(cleaned_ocr, full_text)

            # Extract first information contents
            extracted_fields['FirstInformationContents'] = self._extract_first_information(cleaned_ocr, full_text)

        except Exception as e:
            logger.error(f"Field extraction failed: {str(e)}")

        return extracted_fields

    def _clean_ocr_text(self, ocr_data: List[Dict]) -> List[Dict]:
        """Clean OCR text by removing noise and correcting common OCR errors"""
        cleaned_data = []

        # Common OCR corrections for FIR documents
        corrections = {
            'Fste@': 'District',
            '((aRT': 'Police Station',
            'Sot)': 'Station',
            'staTst': 'Station',
            'AeT@oat': 'Monday',
            '2X': '2 hours',
            'STfeT': 'Street',
            '3fex)': 'Street',
            'TTA,': 'Street',
            '1 Tee aA.': '1 km approx',
            '{81': 'House No',
            'Stel': 'Street',
            'HAN,': 'Hanuman',
            'caleit': 'Colony',
            'Stec,,': 'Street',
            'VoSITENs,,': 'Vishnu Nagar',
            'ailurst,': 'Ailur',
            'SMT': 'Street',
            'Orel': 'Shri',
            'galetaR': 'Gautam',
            '6971': '1997',
            'ASAT': 'Street',
            'dash)': 'District',
            'Ariédt': 'Address',
            'fAreatearan)': 'Father/Husband',
            'Saal': 'Shri',
            'Fel': 'Shri',
            'SAeaa,': 'Shri',
            'Welk': 'Shri',
            'sear': 'Shri',
            'ara)': 'Name',
            'feat:': 'Date',
            '3itet': 'Street',
            '3fex)': 'Street',
            'TTA,': 'Street',
            '1 Tee aA.': '1 km approx',
            'create:': 'District',
            '3itet': 'Street',
            'Rear': 'Present',
            'Ze.': 'No.',
            'det': 'Present',
            'Ze.': 'No.',
            'PATTON': 'Present',
            'feet': 'Address',
            'Pwr': 'Present',
            'faerard': 'Address',
            'HR': 'House',
            'Aelaeael': 'Address',
            'Tat': 'Street',
            'TAT': 'Street',
            'caret': 'Street',
            'attests': 'Address',
            'Yael': 'Street',
            '3a': 'No',
            'ed': 'No',
            '3teTstscla': 'Address',
            'let': 'No',
            'USAT': 'Present',
            'WEN': 'Address',
            'seer': 'Shri',
            'HAT': 'Street',
            'att': 'Street',
            'Hace': 'House',
            'TAT': 'Street',
            'FeV': 'No',
            'Als': 'No',
            'cared': 'Street',
            'Taweg': 'Street',
            'SN.UeT.UE.HoAA': 'S.No.',
            'IL': 'Shri',
            'SOTA': 'Shri',
            'THA': 'Street',
            'Mee': 'Street',
            'SA': 'Street',
            'GOR': 'Street',
            'Use': 'No',
            'TAR': 'Street',
            'ah': 'No',
            'fate': 'Street',
            'act': 'No',
            'fe,': 'No',
            'Ure': 'Present',
            'AT': 'No',
            'Udit': 'Shri',
            'Tale': 'Shri',
            'aired': 'Shri',
            'ale': 'Shri',
            'Aaell': 'Shri',
            'asa)': 'Name',
            'He': 'No',
            'AT': 'No',
            'Udit': 'Shri',
            'Tale': 'Shri',
            'aired': 'Shri',
            'ale': 'Shri',
            'Aaell': 'Shri',
            'asa)': 'Name',
        }

        for item in ocr_data:
            text = item['text'].strip()

            # Skip very short or empty text
            if len(text) < 2:
                continue

            # Remove noise characters
            text = re.sub(r'[^\w\s.,:/()-]', '', text)

            # Apply corrections
            for ocr_error, correction in corrections.items():
                text = text.replace(ocr_error, correction)

            # Clean up multiple spaces
            text = re.sub(r'\s+', ' ', text).strip()

            if text:
                cleaned_data.append({
                    'text': text,
                    'confidence': item.get('confidence', 0),
                    'bbox': item.get('bbox', [])
                })

        return cleaned_data

    def _extract_fir_info(self, ocr_data: List[Dict], full_text: str) -> Dict:
        """Extract basic FIR information"""
        fir_info = {}

        # Extract FIR number - look for 4-digit numbers after FIR patterns
        fir_match = re.search(r'FIR.*?(\d{4})', full_text, re.IGNORECASE)
        if fir_match:
            fir_info['FIRNo'] = fir_match.group(1)

        # Extract date and time of FIR - look for date/time patterns
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})\s*(\d{2}:\d{2})', full_text)
        if date_match:
            fir_info['DateTimeOfFIR'] = f"{date_match.group(1)} {date_match.group(2)}"

        # Extract district - look for "District" followed by text
        district_match = re.search(r'District.*?:(.*?)(?:\s*Police|\s*Station|\s*Year|\s*$)', full_text, re.IGNORECASE)
        if district_match:
            district = district_match.group(1).strip()
            # Clean up and take reasonable length
            district = re.sub(r'[^\w\s]', '', district).strip()
            if len(district) > 2 and len(district) < 50:
                fir_info['District'] = district

        # Extract police station - look for "P.S." or "Police Station"
        ps_match = re.search(r'(?:P\.S\.|Police Station).*?:(.*?)(?:\s*Year|\s*$)', full_text, re.IGNORECASE)
        if ps_match:
            ps = ps_match.group(1).strip()
            ps = re.sub(r'[^\w\s]', '', ps).strip()
            if len(ps) > 2 and len(ps) < 50:
                fir_info['PoliceStation'] = ps

        # Extract year - look for 4-digit year
        year_match = re.search(r'(\d{4})', full_text)
        if year_match:
            year = int(year_match.group(1))
            if 2000 <= year <= 2030:  # Reasonable year range
                fir_info['Year'] = year

        # Extract type of information
        if 'लिखित' in full_text or 'Written' in full_text:
            fir_info['TypeOfInformation'] = 'लिखित'
        elif 'मौखिक' in full_text or 'Oral' in full_text:
            fir_info['TypeOfInformation'] = 'मौखिक'

        return fir_info
    
    
    def _extract_complainant(self, ocr_data: List[Dict], full_text: str) -> Dict:
        """Extract complainant information"""
        complainant = {
            'Name': '',
            'FatherOrHusbandName': '',
            'DOB_YearOfBirth': '',
            'Nationality': 'भारत',
            'UIDNo': '',
            'PassportNo': '',
            'IDDetails': [],
            'Occupation': '',
            'Addresses': [],
            'PhoneNumber': ''
        }

        # Extract name - look for text after "Name" in complainant section
        name_match = re.search(r'Name.*?:(.*?)(?:\s*Father|\s*DOB|\s*Date|\s*$)', full_text, re.IGNORECASE)
        if name_match:
            name = name_match.group(1).strip()
            if len(name) > 2 and len(name) < 100:
                complainant['Name'] = name

        # Extract father's/husband's name
        father_match = re.search(r'(?:Father|Husband).*?(?:Name).*?:(.*?)(?:\s*DOB|\s*Date|\s*$)', full_text, re.IGNORECASE)
        if father_match:
            father_name = father_match.group(1).strip()
            if len(father_name) > 2 and len(father_name) < 100:
                complainant['FatherOrHusbandName'] = father_name

        # Extract DOB/Year of birth - look for 4-digit years in reasonable range
        dob_match = re.search(r'(?:DOB|Birth).*?(\d{4})', full_text, re.IGNORECASE)
        if dob_match:
            year = int(dob_match.group(1))
            if 1900 <= year <= 2010:  # Reasonable birth year range
                complainant['DOB_YearOfBirth'] = str(year)

        # Extract mobile number - look for 10-digit numbers
        mobile_match = re.search(r'(\d{10})', full_text)
        if mobile_match:
            complainant['PhoneNumber'] = mobile_match.group(1)

        # Extract UID number - look for 12-digit numbers
        uid_match = re.search(r'(\d{12})', full_text)
        if uid_match:
            complainant['UIDNo'] = uid_match.group(1)

        # Extract addresses - look for address patterns
        address_match = re.search(r'Address.*?:(.*?)(?:\s*Phone|\s*Mobile|\s*$)', full_text, re.IGNORECASE)
        if address_match:
            address = address_match.group(1).strip()
            if len(address) > 5 and len(address) < 200:
                complainant['Addresses'] = [{'Type': 'Present Address', 'Address': address}]

        return complainant
    
    def _extract_accused(self, ocr_data: List[Dict]) -> List[Dict]:
        """Extract accused details"""
        accused_list = []
        
        # Find accused section
        accused_started = False
        current_accused = None
        
        for item in ocr_data:
            text = item['text']
            
            if 'Accused' in text or 'आरोपी' in text:
                accused_started = True
                if current_accused:
                    accused_list.append(current_accused)
                current_accused = {
                    'Name': '',
                    'Alias': '',
                    'RelativeName': '',
                    'PresentAddress': ''
                }
            elif accused_started and current_accused:
                # Extract accused details
                if 'Name' in text or 'नाव' in text:
                    # Next item likely has the name
                    continue
                elif text and len(text) > 3 and not current_accused['Name']:
                    current_accused['Name'] = text
        
        if current_accused and current_accused['Name']:
            accused_list.append(current_accused)
        
        return accused_list

    def _load_improved_patterns(self):
        """Load improved patterns from training data"""
        try:
            from pathlib import Path
            import json

            pattern_file = Path("training_data") / "improved_patterns.json"
            if pattern_file.exists():
                with pattern_file.open('r', encoding='utf-8') as f:
                    improved_patterns = json.load(f)
                    self.patterns.update(improved_patterns)
                    logger.info(f"Loaded {len(improved_patterns)} improved patterns")
        except Exception as e:
            logger.warning(f"Could not load improved patterns: {str(e)}")
    
    def _extract_occurrence(self, ocr_data: List[Dict], full_text: str) -> Dict:
        """Extract occurrence details"""
        occurrence = {
            'Day': '',
            'DateFrom': '',
            'DateTo': '',
            'TimePeriod': '',
            'TimeFrom': '',
            'TimeTo': ''
        }

        # Extract day - look for day names
        day_match = re.search(r'Day.*?:(.*?)(?:\s*Date|\s*$)', full_text, re.IGNORECASE)
        if day_match:
            day = day_match.group(1).strip()
            if len(day) > 2 and len(day) < 20:
                occurrence['Day'] = day

        # Extract dates - look for date patterns
        dates = re.findall(r'(\d{2}/\d{2}/\d{4})', full_text)
        if len(dates) >= 1:
            occurrence['DateFrom'] = dates[0]
        if len(dates) >= 2:
            occurrence['DateTo'] = dates[1]

        # Extract time period - look for time-related text
        time_period_match = re.search(r'Time.*?Period.*?:(.*?)(?:\s*Time|\s*$)', full_text, re.IGNORECASE)
        if time_period_match:
            period = time_period_match.group(1).strip()
            if len(period) > 1 and len(period) < 50:
                occurrence['TimePeriod'] = period

        # Extract times - look for time patterns
        times = re.findall(r'(\d{2}:\d{2})', full_text)
        if len(times) >= 1:
            occurrence['TimeFrom'] = times[0]
        if len(times) >= 2:
            occurrence['TimeTo'] = times[1]

        return occurrence
    
    def _extract_acts_sections(self, ocr_data: List[Dict], full_text: str) -> List[Dict]:
        """Extract acts and sections"""
        acts_sections = []

        # Look for section numbers in the text
        section_matches = re.findall(r'(?:Section|BNS).*?(\d+)', full_text, re.IGNORECASE)
        for section in section_matches:
            acts_sections.append({
                'Act': 'भारतीय न्याय संहिता (बी एन एस), 2023',
                'Section': section.strip()
            })

        # If no sections found, look for any standalone numbers that might be sections
        if not acts_sections:
            # Look for patterns like "173" in the context of acts
            potential_sections = re.findall(r'\b(\d{2,3})\b', full_text)
            for num in potential_sections:
                num_int = int(num)
                if 100 <= num_int <= 511:  # Reasonable section number range
                    acts_sections.append({
                        'Act': 'भारतीय न्याय संहिता (बी एन एस), 2023',
                        'Section': num
                    })
                    break  # Just take the first reasonable one

        return acts_sections
    
    def _extract_place(self, ocr_data: List[Dict], full_text: str) -> Dict:
        """Extract place of occurrence"""
        place = {
            'DirectionDistanceFromPS': {
                'Direction': '',
                'Distance': ''
            },
            'BeatNo': '',
            'Address': '',
            'DistrictState': ''
        }

        # Extract direction and distance - look for patterns in place section
        direction_match = re.search(r'Direction.*?:(.*?)(?:\s*Distance|\s*Beat|\s*$)', full_text, re.IGNORECASE)
        if direction_match:
            direction = direction_match.group(1).strip()
            if len(direction) > 2 and len(direction) < 100:
                place['DirectionDistanceFromPS']['Direction'] = direction

        # Extract distance
        distance_match = re.search(r'Distance.*?:(.*?)(?:\s*Beat|\s*Address|\s*$)', full_text, re.IGNORECASE)
        if distance_match:
            distance = distance_match.group(1).strip()
            if len(distance) > 1 and len(distance) < 50:
                place['DirectionDistanceFromPS']['Distance'] = distance

        # Extract beat number
        beat_match = re.search(r'Beat.*?:(.*?)(?:\s*Address|\s*$)', full_text, re.IGNORECASE)
        if beat_match:
            beat = beat_match.group(1).strip()
            if len(beat) > 0 and len(beat) < 20:
                place['BeatNo'] = beat

        # Extract address - look for address patterns
        address_match = re.search(r'Address.*?:(.*?)(?:\s*District|\s*State|\s*$)', full_text, re.IGNORECASE)
        if address_match:
            address = address_match.group(1).strip()
            if len(address) > 5 and len(address) < 200:
                place['Address'] = address

        return place
    
    def _extract_action_taken(self, ocr_data: List[Dict], full_text: str) -> Dict:
        """Extract action taken details"""
        action_taken = {
            'RegisteredCaseInvestigation': {
                'OfficerName': '',
                'Rank': '',
                'No': ''
            },
            'DirectedNameOfIO': '',
            'DirectedRank': '',
            'DirectedNo': '',
            'RefusedInvestigationDueTo': '',
            'TransferredPS': '',
            'TransferredDistrict': '',
            'ROAC': ''
        }

        # Extract officer name - look for name patterns in action section
        officer_match = re.search(r'(?:Officer|Name).*?:(.*?)(?:\s*Rank|\s*$)', full_text, re.IGNORECASE)
        if officer_match:
            name = officer_match.group(1).strip()
            if len(name) > 2 and len(name) < 100:
                action_taken['RegisteredCaseInvestigation']['OfficerName'] = name

        # Extract rank
        rank_match = re.search(r'Rank.*?:(.*?)(?:\s*No|\s*$)', full_text, re.IGNORECASE)
        if rank_match:
            rank = rank_match.group(1).strip()
            if len(rank) > 2 and len(rank) < 50:
                action_taken['RegisteredCaseInvestigation']['Rank'] = rank

        # Extract officer number
        no_match = re.search(r'No.*?:(.*?)(?:\s*$)', full_text, re.IGNORECASE)
        if no_match:
            no = no_match.group(1).strip()
            if len(no) > 0 and len(no) < 20:
                action_taken['RegisteredCaseInvestigation']['No'] = no

        return action_taken

    def _extract_first_information(self, ocr_data: List[Dict], full_text: str) -> str:
        """Extract first information contents"""
        # Look for content after "First Information Contents" or similar patterns
        content_match = re.search(r'(?:First\s*Information\s*Contents|प्रथम\s*खबर\s*अंतर्गत).*?:(.*?)(?:Action\s*Taken|$)', full_text, re.IGNORECASE | re.DOTALL)
        if content_match:
            return content_match.group(1).strip()

        # Try to find content between complainant signature and action taken
        return ""

    def _extract_accused(self, ocr_data: List[Dict]) -> List[Dict]:
        """Extract accused details"""
        accused_list = []

        # Look for accused section in the text
        full_text = ' '.join([item['text'] for item in ocr_data])

        # Find accused names - look for patterns after "Accused" or "आरोपी"
        accused_matches = re.findall(r'(?:Accused|आरोपी).*?(?:Name|नाव).*?:(.*?)(?:Alias|उपनाव|$)', full_text, re.IGNORECASE)
        for name in accused_matches:
            if name.strip():
                accused_list.append({
                    'Name': name.strip(),
                    'Alias': '',
                    'RelativeName': '',
                    'PresentAddress': ''
                })

        return accused_list