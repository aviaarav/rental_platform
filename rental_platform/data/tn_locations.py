"""Tamil Nadu districts and their taluks (used for the dependent dropdowns).

You can add or correct any taluk in this dictionary later; the dropdowns update automatically.
"""

TN_LOCATIONS = {
    'Ariyalur': ['Ariyalur', 'Sendurai', 'Udayarpalayam', 'Andimadam'],
    'Chengalpattu': ['Chengalpattu', 'Tambaram', 'Pallavaram', 'Vandalur', 'Madurantakam', 'Cheyyur', 'Thirukalukundram', 'Tiruporur'],
    'Chennai': ['Alandur', 'Ambattur', 'Aminjikarai', 'Ayanavaram', 'Egmore', 'Guindy', 'Madhavaram', 'Maduravoyal', 'Mambalam', 'Mylapore', 'Perambur', 'Purasawalkam', 'Sholinganallur', 'Thiruvottiyur', 'Tondiarpet', 'Velachery'],
    'Coimbatore': ['Coimbatore North', 'Coimbatore South', 'Annur', 'Kinathukadavu', 'Madukkarai', 'Mettupalayam', 'Perur', 'Pollachi', 'Sulur', 'Valparai'],
    'Cuddalore': ['Cuddalore', 'Bhuvanagiri', 'Chidambaram', 'Kattumannarkoil', 'Kurinjipadi', 'Panruti', 'Srimushnam', 'Tittakudi', 'Virudhachalam'],
    'Dharmapuri': ['Dharmapuri', 'Harur', 'Karimangalam', 'Nallampalli', 'Palacode', 'Pennagaram'],
    'Dindigul': ['Dindigul East', 'Dindigul West', 'Athoor', 'Kodaikanal', 'Natham', 'Nilakottai', 'Oddanchatram', 'Palani', 'Vedasandur'],
    'Erode': ['Erode', 'Anthiyur', 'Bhavani', 'Gobichettipalayam', 'Kodumudi', 'Modakurichi', 'Nambiyur', 'Perundurai', 'Sathyamangalam', 'Thalavadi'],
    'Kallakurichi': ['Kallakurichi', 'Chinnasalem', 'Kalvarayan Hills', 'Sankarapuram', 'Tirukoilur', 'Ulundurpet'],
    'Kancheepuram': ['Kancheepuram', 'Kundrathur', 'Sriperumbudur', 'Uthiramerur', 'Walajabad'],
    'Kanyakumari': ['Agastheeswaram', 'Kalkulam', 'Killiyoor', 'Thiruvattar', 'Thovalai', 'Vilavancode'],
    'Karur': ['Karur', 'Aravakurichi', 'Kadavur', 'Krishnarayapuram', 'Kulithalai', 'Manmangalam', 'Pugalur'],
    'Krishnagiri': ['Krishnagiri', 'Anchetty', 'Bargur', 'Denkanikottai', 'Hosur', 'Pochampalli', 'Shoolagiri', 'Uthangarai'],
    'Madurai': ['Madurai North', 'Madurai South', 'Madurai East', 'Madurai West', 'Kalligudi', 'Melur', 'Peraiyur', 'Sholavandan', 'Thirumangalam', 'Thiruparankundram', 'Usilampatti', 'Vadipatti'],
    'Mayiladuthurai': ['Mayiladuthurai', 'Kuthalam', 'Sirkazhi', 'Tharangambadi'],
    'Nagapattinam': ['Nagapattinam', 'Kilvelur', 'Thirukkuvalai', 'Vedaranyam'],
    'Namakkal': ['Namakkal', 'Kolli Hills', 'Kumarapalayam', 'Mohanur', 'Paramathi Velur', 'Rasipuram', 'Sendamangalam', 'Tiruchengode'],
    'Nilgiris': ['Udhagamandalam', 'Coonoor', 'Gudalur', 'Kotagiri', 'Kundah', 'Pandalur'],
    'Perambalur': ['Perambalur', 'Alathur', 'Kunnam', 'Veppanthattai'],
    'Pudukkottai': ['Pudukkottai', 'Alangudi', 'Aranthangi', 'Avudaiyarkoil', 'Gandarvakottai', 'Iluppur', 'Karambakudi', 'Kulathur', 'Manamelkudi', 'Ponnamaravathy', 'Thirumayam', 'Viralimalai'],
    'Ramanathapuram': ['Ramanathapuram', 'Kadaladi', 'Kamuthi', 'Mudukulathur', 'Paramakudi', 'Rajasingamangalam', 'Rameswaram', 'Tiruvadanai'],
    'Ranipet': ['Ranipet', 'Arakkonam', 'Arcot', 'Kalavai', 'Nemili', 'Sholinghur', 'Walajapet'],
    'Salem': ['Salem', 'Attur', 'Edappadi', 'Gangavalli', 'Kadayampatti', 'Mettur', 'Omalur', 'Pethanayakkanpalayam', 'Salem South', 'Salem West', 'Sankagiri', 'Vazhapadi', 'Yercaud'],
    'Sivaganga': ['Sivaganga', 'Devakottai', 'Ilayangudi', 'Kalaiyarkovil', 'Karaikudi', 'Manamadurai', 'Singampunari', 'Thirupathur', 'Thirupuvanam'],
    'Tenkasi': ['Tenkasi', 'Alangulam', 'Kadayanallur', 'Sankarankovil', 'Shenkottai', 'Sivagiri', 'Thiruvengadam', 'Veerakeralampudur'],
    'Thanjavur': ['Thanjavur', 'Ammapettai', 'Budalur', 'Kumbakonam', 'Orathanadu', 'Papanasam', 'Pattukkottai', 'Peravurani', 'Thiruvaiyaru', 'Thiruvidaimarudur'],
    'Theni': ['Theni', 'Andipatti', 'Bodinayakanur', 'Periyakulam', 'Uthamapalayam'],
    'Thoothukudi': ['Thoothukudi', 'Eral', 'Ettayapuram', 'Kayathar', 'Kovilpatti', 'Ottapidaram', 'Sathankulam', 'Srivaikuntam', 'Tiruchendur', 'Vilathikulam'],
    'Tiruchirappalli': ['Tiruchirappalli East', 'Tiruchirappalli West', 'Lalgudi', 'Manachanallur', 'Manapparai', 'Marungapuri', 'Musiri', 'Srirangam', 'Thiruverumbur', 'Thottiyam', 'Thuraiyur'],
    'Tirunelveli': ['Tirunelveli', 'Ambasamudram', 'Cheranmahadevi', 'Manur', 'Nanguneri', 'Palayamkottai', 'Radhapuram', 'Thisayanvilai'],
    'Tirupathur': ['Tirupathur', 'Ambur', 'Natrampalli', 'Vaniyambadi'],
    'Tiruppur': ['Tiruppur North', 'Tiruppur South', 'Avinashi', 'Dharapuram', 'Kangeyam', 'Madathukulam', 'Palladam', 'Udumalaipettai', 'Uthukuli'],
    'Tiruvallur': ['Tiruvallur', 'Ambattur', 'Avadi', 'Gummidipoondi', 'Madhavaram', 'Pallipattu', 'Ponneri', 'Poonamallee', 'Tiruttani', 'Uthukottai'],
    'Tiruvannamalai': ['Tiruvannamalai', 'Arni', 'Chengam', 'Chetpet', 'Cheyyar', 'Jamunamarathur', 'Kalasapakkam', 'Kilpennathur', 'Polur', 'Thandrampet', 'Vandavasi', 'Vembakkam'],
    'Tiruvarur': ['Tiruvarur', 'Kodavasal', 'Koothanallur', 'Mannargudi', 'Nannilam', 'Needamangalam', 'Thiruthuraipoondi', 'Valangaiman'],
    'Vellore': ['Vellore', 'Anaicut', 'Gudiyatham', 'K.V. Kuppam', 'Katpadi', 'Pernambut'],
    'Viluppuram': ['Viluppuram', 'Gingee', 'Kandachipuram', 'Marakkanam', 'Melmalayanur', 'Thiruvennainallur', 'Tindivanam', 'Vanur', 'Vikravandi'],
    'Virudhunagar': ['Virudhunagar', 'Aruppukottai', 'Kariapatti', 'Rajapalayam', 'Sattur', 'Sivakasi', 'Srivilliputhur', 'Tiruchuli', 'Vembakottai', 'Watrap'],
}

DISTRICTS = sorted(TN_LOCATIONS.keys())


def get_taluks(district):
    """Taluk list for a district (empty list for an unknown district)."""
    return TN_LOCATIONS.get(district, [])


def is_valid_location(district, taluk):
    """True when the taluk really belongs to the district."""
    return taluk in TN_LOCATIONS.get(district, [])