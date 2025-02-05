import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from services.searchv2 import EnhancedSearchService
from services.llm import LLMService
from services.evaluation import EnhancedEvaluator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up API keys
PINECONE_API_KEY = '946c3781-26d7-4e46-a778-5262d54403f8'
OPEN_AI_EMBEDDING_API_KEY = "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"
OPENAI_API_KEY = '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'

# Tags dictionary for metadata enhancement
tags = {
    "pests": [
        "Alfalfa Weevil", "aphid", "aphids", "Apple Maggot", "Armyworms", "Common Armyworm",
        "Aster Leafhopper", "Bean Leaf Beetle", "beetle", "Bindweed", "Black Cutworm",
        "Brown Marmorated Stink Bug", "Cabbage Looper", "Cabbage Worms", "Carrot Weevil",
        "Cereal Leaf Beetle", "Codling Moth", "Colorado Potato Beetle", "Common Stalk Borer",
        "corn root worm", "corn rootworm", "Corn Rootworm", "Cucumber Beetles", "cutworm",
        "Diamondback Moth", "Diamondback Moth Larvae", "Early Blight", "egg", "Emerald Ash Borer",
        "European Corn Borer", "Fall Armyworm", "Flea Beetles", "fly", "foxtails", "Giant Ragweed",
        "Grasshoppers", "Green Cloverworm", "Gypsy Moth", "Hornworms", "Imported Cabbageworm",
        "Japanese Beetle", "juvenile", "Lamb's Quarters", "larva", "Late Blight", "leafhopper",
        "maggots", "Mexican Bean Beetle", "mite", "moth", "Onion Thrips", "Pepper Maggot", "pest",
        "Pigweed", "Plum Curculio", "Potato Leafhopper", "Potato Scab", "ragweed",
        "Root Lesion Nematodes", "Rootworms", "Seedcorn Maggots", "Slugs", "Soybean Aphids",
        "Soybean Cyst Nematode", "Spider Mites", "Spotted Wing Drosophila", "Squash Bug",
        "Stink Bugs", "Swede Midge", "Tarnished Plant Bug", "thrips", "Tomato Hornworm",
        "True Armyworm", "Two-Spotted Spider Mite", "Vegetable Leafminers", "Velvetleaf",
        "Western Bean Cutworm", "Western Flower Thrips", "White Grubs", "Wireworms",
        "Zebra Caterpillar"
    ],
    "crops": [
        "alfalfa", "annual ryegrass", "apples", "aronia berries", "asparagus", "barley", "beans",
        "beet", "blueberries", "broccoli", "brussels sprouts", "buckwheat", "cabbage", "canola",
        "carrot", "cauliflower", "celery", "cherries", "christmas trees", "clover", "cole crops",
        "corn", "cover crop", "cranberries", "crimson clover", "crop", "currants", "eggplants",
        "elderberries", "field corn", "field peas", "forage", "garlic", "ginseng", "grapes",
        "greenhouse vegetables", "green peas", "hairy vetch", "hay", "hemp", "hops",
        "industrial hemp", "kale", "kohlrabi", "leafy greens", "lettuce", "maple syrup", "mint",
        "mushrooms", "native plants", "nursery crops", "oats", "onions", "orchardgrass",
        "ornamentals", "parsnips", "pears", "peas", "plums", "potatoes", "processing vegetables",
        "pumpkins", "radish cover crop", "raddish", "raspberries", "red clover", "rutabaga",
        "rye", "seed corn", "silage corn", "snap beans", "snap peas", "sorghum", "soybeans",
        "spinach", "squash", "strawberries", "sugar beets", "sunflower", "sweet corn",
        "sweet potatoes", "table grapes", "tart cherries", "timothy", "tobacco", "tomatoes",
        "triticale", "turnips", "wheat", "wine grapes", "winter rye", "winter wheat",
        "winter wheat cover"
    ],
    "management_practices": [
        "application", "beneficial", "beneficial insects", "biological control", "biopesticides",
        "chemical control", "competition", "conservation", "conservation tillage", "control",
        "cover crop termination", "crop rotation", "cultural practices", "degree day",
        "degree day modeling", "drone monitoring", "early planting", "economic thresholds",
        "emergency pest management", "field sanitation", "food safety certification",
        "frost protection", "GAP certification", "genetic resistance", "habitat manipulation",
        "harvest", "herbicide", "integrated pest management", "IPM", "irrigation scheduling",
        "label", "management practices", "manure management", "mechanical control", "monitoring",
        "natural enemies", "nutrient management planning", "organic certification", "percentage",
        "pest control", "pest forecasting", "pesticide", "planting", "pollinator protection",
        "precision agriculture", "prevention", "refuge requirements", "resistance",
        "resistance management", "rotation", "satellite imagery", "scouting", "seed", "seeding",
        "soil moisture monitoring", "spray", "strip tillage", "threshold",
        "threshold-based decision making", "timing", "trap crops", "treatment",
        "variable rate application", "weed", "weed control", "winter spreading",
        "application records", "data collection", "field records", "record keeping",
        "soil testing records", "yield monitoring", "documentation", "compliance records",
        "spray records", "weather records", "crop planning", "succession planting",
        "fertility planning", "integrated pest management planning", "conservation planning",
        "seasonal planning", "rotational planning", "equipment scheduling", "irrigation planning",
        "nutrient budgeting", "crop insurance", "disease forecasting", "weather monitoring",
        "market planning", "storage management", "risk assessment", "contingency planning",
        "disaster preparedness", "worker training", "safety protocols", "equipment training",
        "product grading", "quality testing", "storage monitoring", "contamination prevention",
        "quality assurance", "quality control", "sampling protocols", "inspection procedures",
        "batch tracking", "post-harvest handling", "equipment maintenance", "facility management",
        "harvest timing", "integrated crop management", "pest scouting protocols",
        "resource allocation", "sanitation procedures", "waste management", "water management",
        "workflow optimization"
    ],
    "regions": [
        "wisconsin", "midwest", "great plains", "upper midwest", "illinois", "iowa",
        "minnesota", "michigan", "north dakota", "south dakota", "northern highlands",
        "central plain", "central sands", "chippewa valley", "door peninsula", "driftless area",
        "eastern ridges", "fox river valley", "glaciated southeast", "kettle moraine",
        "kickapoo valley", "lake superior lowland", "lowlands", "manitowoc plains",
        "milwaukee river basin", "mississippi river valley", "niagara escarpment",
        "northern highlands", "northwest sands", "pecatonica river", "red clay region",
        "rock river basin", "root river watershed", "st croix river valley", "sugar river basin",
        "superior coastal plain", "tension zone", "wisconsin", "wisconsin river valley",
        "wolf river basin", "yahara river watershed"
    ],

    "soil_management": [
        "aggregate stability", "alkalinity", "beneficial soil organisms", "biochar",
        "buffer strips", "bulk density", "cation exchange capacity", "clay soils",
        "compaction testing", "composting", "contour plowing", "cover crop selection",
        "cover cropping", "deep tillage", "drainage management", "erosion control",
        "erosion prevention", "fertilizer", "fertilizer application timing",
        "fertilizer placement", "field capacity", "frost depth monitoring",
        "frost heaving management", "glacial till", "humus", "infiltration rate",
        "irrigation scheduling", "karst topography management", "leaching prevention",
        "lime application", "loess soils", "manure", "manure application timing",
        "manure management", "manure nutrient testing", "microbial activity",
        "microbiome assessment", "micronutrient testing", "micronutrients",
        "minimum tillage", "moisture monitoring", "muck soils", "mulching",
        "nitrate leaching", "nitrate testing", "nitrogen", "nitrogen application timing",
        "nitrogen use efficiency", "no-till", "NPK", "nutrient cycling",
        "nutrient loss prevention", "nutrient trading", "organic amendments",
        "organic matter", "organic matter testing", "peat soils", "penetration resistance",
        "permeability", "pH", "pH adjustment", "phosphorus", "phosphorus index",
        "phosphorus runoff risk", "potassium", "reduced tillage", "residue management",
        "riparian zones", "salinity", "salinity testing", "sandy soils",
        "snowmelt management", "soil amendment", "soil biodiversity",
        "soil carbon sequestration", "soil compaction", "soil conservation", "soil cover",
        "soil drainage class", "soil erosion assessment", "soil fertility",
        "soil fertility testing", "soil health assessment", "soil health testing",
        "soil mapping", "soil microbiome", "soil moisture retention", "soil nutrient",
        "soil nutrient testing", "soil organic carbon", "soil organic matter testing",
        "soil porosity", "soil quality", "soil sampling", "soil sampling depth",
        "soil sampling frequency", "soil sampling grid", "soil structure",
        "soil temperature monitoring", "soil testing protocols", "soil texture",
        "soil texture analysis", "spring soil preparation", "spring thaw management",
        "strip cropping", "subsoil management", "surface runoff management",
        "terrace farming", "tile drainage", "tile drainage spacing", "tillage",
        "tillage depth", "tillage timing", "topsoil depth", "vertical tillage",
        "water holding capacity", "water retention", "watershed protection",
        "wilting point", "winter cover", "winter soil protection", "zone tillage"
    ],
    "crop_health": [
        "abiotic stress", "alfalfa winter survival", "anthracnose", "apple scab",
        "bacterial diseases", "bacterial leaf streak", "bacterial spot", "blight",
        "boron deficiency", "boron toxicity", "brown stem rot", "cankers", "chlorosis",
        "climate resilience", "cranberry fruit rot", "crop damage", "crop protection",
        "crop scouting", "disease", "disease resistance", "downy mildew",
        "drought stress", "early detection", "fire blight", "frost damage",
        "fungal diseases", "fungicide", "fertilizer application", "goss's wilt",
        "gray leaf spot", "growing degree days", "heat stress", "ice damage",
        "integrated crop health management", "iron chlorosis", "irrigation management",
        "leaf blight", "leaf curling", "leaf spot", "lodging", "necrosis",
        "nematodes", "northern corn leaf blight", "nutrient deficiency",
        "pest resistance", "plant diagnostics", "plant health", "plant vigor",
        "powdery mildew", "purple stems", "root rot", "rot", "rust", "scab",
        "snow mold", "soil testing", "spring green-up", "stem rot", "stress",
        "stunted growth", "sudden death syndrome", "tar spot", "viral diseases",
        "waterlogging", "white mold", "wilt", "winter desiccation", "winter kill",
        "yellowing leaves", "yield", "yield loss", "zinc deficiency", "emergence rate",
        "germination vigor", "growth stage assessment", "maturity timing",
        "pollination success", "reproductive stage", "seedling vigor",
        "stand establishment", "tasseling stage", "tillering assessment",
        "vegetative growth", "angular leaf spot", "bacterial wilt", "blackleg",
        "cercospora leaf spot", "clubroot", "common rust", "crown rot", "eyespot",
        "fusarium head blight", "green stem disorder", "head scab", "leaf rust",
        "northern leaf blight", "phytophthora root rot", "pythium root rot",
        "rhizoctonia", "septoria leaf spot", "southern rust", "stalk rot",
        "stem canker", "stewart's wilt", "stripe rust", "sudden death", "take-all",
        "verticillium wilt", "blossom end rot", "calcium deficiency", "cold injury",
        "copper deficiency", "fertilizer burn", "flower abortion", "frost heaving",
        "herbicide injury", "hollow heart", "magnesium deficiency",
        "manganese deficiency", "molybdenum deficiency", "nitrogen deficiency",
        "phosphorus deficiency", "potassium deficiency", "salt injury",
        "sulfur deficiency", "sunscald", "tip burn", "chlorophyll measurement",
        "disease incidence", "disease severity", "drone imaging", "field assessment",
        "infrared imaging", "leaf analysis", "NDVI measurement", "nutrient analysis",
        "plant tissue testing", "root assessment", "sap analysis",
        "seed quality testing", "soil pathogen testing", "spectral analysis",
        "stress detection", "tissue sampling", "visual assessment",
        "yield estimation", "yield mapping"
    ],
    "life_stages": [
        "adult", "egg", "emergence", "flowering", "fruiting", "germination", "grain fill",
        "juvenile", "larva", "mature", "nymph", "pollination", "pupa", "reproductive",
        "ripening", "seedling", "senescence", "shooting", "silking", "tasseling",
        "tillering", "vegetative"
    ],
    "time_period": [
        "annual", "autumn", "biennial", "bloom time", "dormant season", "early season",
        "fall", "first frost", "growing season", "harvest period", "last frost",
        "late season", "mid season", "monthly", "off season", "perennial",
        "planting date", "post emergence", "post harvest", "pre emergence",
        "pre harvest", "pre plant", "spring", "summer", "winter"
    ],
    "metrics_measurements": [
        "acres", "biomass", "bushels", "cation exchange capacity", "concentration",
        "disease severity", "economic threshold", "fertility index", "germination rate",
        "grain moisture", "growth rate", "humidity", "infiltration rate",
        "injury level", "moisture content", "nutrient concentration",
        "organic matter percentage", "parts per million", "pest density",
        "pH level", "plant population", "precipitation", "pressure",
        "relative humidity", "soil temperature", "survival rate", "temperature",
        "threshold level", "tons per acre", "yield per acre"
    ]
}


async def run_comparison(test_cases: List[Dict[str, str]], tags: Dict[str, List[str]]):
    """
    Run comparison between GPT and RAG approaches with enhanced search.
    """
    try:
        # Initialize services
        search_service = EnhancedSearchService(
            pinecone_api_key=PINECONE_API_KEY,
            openai_embedding_key=OPEN_AI_EMBEDDING_API_KEY,
            tag_categories=tags
        )

        llm_service = LLMService(
            openai_api_key=OPENAI_API_KEY,
            mcp_params=None
        )

        # Test connection
        test_results = await search_service.semantic_search("test query", top_k=1)
        logger.info(f"Connection test completed: {len(test_results)} results found")

        # Initialize evaluator once
        evaluator = EnhancedEvaluator()

        # Single loop through test cases
        for test_case in test_cases:
            query = test_case["query"]
            reference = test_case.get("reference")

            logger.info(f"\n{'=' * 50}")
            logger.info(f"Testing query: {query}")
            logger.info(f"{'=' * 50}")

            # 1. Direct GPT Response
            logger.info("\nGetting GPT response...")
            try:
                gpt_response = llm_service.chat_with_openai(query)

                # Evaluate GPT response
                if reference:
                    gpt_metrics = evaluator.evaluate_response(gpt_response, reference)
                    print("\nGPT Evaluation Results:")
                    evaluator.print_evaluation_results(gpt_metrics)

            except Exception as e:
                logger.error(f"Error in GPT response: {e}")
                gpt_response = None

            # 2. RAG Response
            logger.info("\nGetting RAG response...")
            try:
                search_results = await search_service.semantic_search(query, top_k=3)
                rag_prompt = llm_service.generate_rag_prompt(query, search_results)
                rag_response = llm_service.chat_with_openai(rag_prompt)

                # Evaluate RAG response
                if reference:
                    rag_metrics = evaluator.evaluate_response(rag_response, reference)
                    print("\nRAG Evaluation Results:")
                    evaluator.print_evaluation_results(rag_metrics)

            except Exception as e:
                logger.error(f"Error in RAG process: {str(e)}", exc_info=True)
                rag_response = None

            # Display Reference Answer
            if reference:
                print("\nReference Answer:")
                print("-" * 40)
                print(reference)

            print("\n" + "=" * 50 + "\n")

    except Exception as e:
        logger.error(f"Error during comparison: {e}", exc_info=True)

    # Example test cases
    # test_cases = [
    # {
    #     "query": "What is the biggest pest for Corn?",
    #     "reference": """The biggest pests for corn in Wisconsin are often western corn rootworm and European corn borer.
    #                     Monitoring populations and rotating crops are critical strategies to reduce infestations."""
    # },
    # {
    #     "query": "I'm trying to make a pest management plan, what should I look out for this summer?",
    #     "reference": """Common pests to watch for include western corn rootworm, soybean aphids, and Japanese beetles.
    #                     Scout weekly and use thresholds to determine management actions."""
    # },
    # {
    #     "query": "What would the recommendation be for dealing with aphids in my corn fields?",
    #     "reference": """Corn leaf aphids rarely require treatment in Wisconsin field corn.
    #                     Scout during tasseling as heavy infestations can impact pollination.
    #                     Treatment may be warranted if 50% of plants have more than 400 aphids per plant during tasseling,
    #                     particularly under drought conditions."""
    # },
    # {
    #     "query": "How do I manage soybean aphid?",
    #     "reference": """Monitor soybean fields starting in late June, focusing on aphid populations.
    #                     Apply insecticides when populations exceed the economic threshold of 250 aphids per plant
    #                     on 80% of the plants in the R1-R5 growth stages."""
    # },
    # {
    #     "query": "What can I spray on soybean aphids in Wisconsin?",
    #     "reference": """Effective insecticides include pyrethroids and organophosphates.
    #                     Follow label recommendations and consider resistance management by rotating modes of action."""
    # },
    # {
    #     "query": "When do I sweep for leafhoppers?",
    #     "reference": """Start sweeping for leafhoppers in alfalfa fields during late spring and early summer.
    #                     Thresholds are 20 leafhoppers per 10 sweeps for uncut alfalfa and 50 leafhoppers per 10 sweeps for regrowth."""
    # },
    # {
    #     "query": "What type of damage does Japanese beetle do to corn?",
    #     "reference": """Japanese beetles cause damage by defoliating leaves and feeding on corn silks.
    #                     Silk clipping can interfere with pollination if it reduces silks below ½ inch before pollination is complete."""
    # },
    # {
    #     "query": "What insects are a problem in blooming soybeans?",
    #     "reference": """Key pests include Japanese beetles, soybean aphids, and stink bugs.
    #                     Scout regularly during the blooming stage and address pests exceeding economic thresholds."""
    # },
    # {
    #     "query": "What is the economic threshold for Japanese beetles on soybeans?",
    #     "reference": """The economic threshold is 30% defoliation prior to bloom and 20% defoliation from bloom to pod-fill stages."""
    # },
    # {
    #     "query": "When should I start scouting for alfalfa leaf hopper?",
    #     "reference": """Begin scouting for alfalfa leafhoppers after the first cutting of alfalfa.
    #                     Use sweep nets to monitor populations and treat if populations exceed 20 per 10 sweeps."""
    # },
    # {
    #     "query": "What are the main pests that I should be scouting for in winter wheat?",
    #     "reference": """Common pests in winter wheat include cereal leaf beetles, aphids, and armyworms.
    #                     Scout fields during the growing season and manage pests based on thresholds."""
    # },
    # {
    #     "query": "Is soybean gall midge going to be a concern soon?",
    #     "reference": """Soybean gall midge is an emerging pest, with sporadic reports in surrounding states.
    #                     Monitor research updates and consider early-season scouting near field edges."""
    # },
    # {
    #     "query": "Why isn't my corn resistant to western corn rootworm anymore?",
    #     "reference": """Resistance to Bt corn hybrids has been reported in some western corn rootworm populations.
    #                     Consider rotating to non-corn crops and using non-Bt hybrids with soil-applied insecticides."""
    # },
    # {
    #     "query": "Why was alfalfa weevil so bad in 2024?",
    #     "reference": """Mild winter conditions and early spring temperatures likely favored high populations of alfalfa weevils in 2024.
    #                     Timely scouting and early cutting are critical for managing infestations."""
    # },
    # {
    #     "query": "What is the specific infestation threshold for western bean cutworm field or sweet "
    #              "corn that should trigger an insecticide application?",
    #     "reference": """Treatment is recommended if 8% of plants have egg masses or small larvae in field or sweet corn."""
    # },
    # {
    #     "query": "What is the insecticide reapplication interval (in days) on silking sweet corn to control corn "
    #              "earworm in Wisconsin?",
    #     "reference": """Reapply insecticides every 3–5 days during silking to manage corn earworm populations effectively."""
    # },
    # {
    #     "query": "What is the insecticide reapplication interval (in days) on silking sweet corn to control corn "
    #              "earworm when adult trap captures exceed 50 moths per night using pheromone traps in Wisconsin?",
    #     "reference": """When trap captures exceed 50 moths per night, reapply insecticides every 3 days during silking."""
    # },
    # {
    #     "query": "What is the insecticide reapplication interval (in days) on silking sweet corn to control corn "
    #              "earworm when adult captures exceed 200 moths per night using pheromone traps in Wisconsin?",
    #     "reference": """If trap captures exceed 200 moths per night, reapply insecticides every 2–3 days during silking."""
    # }
    #     {"query":"What can I spray on soybean aphids",
    #      "reference": """"""
    #     }


if __name__ == "__main__":
    # Example test cases
    test_cases = [
        {
            "query": "When should I scout for root protection following corn planting?",
            "reference": """how to scout: Count the number of 
CRW beetles on 50 corn plants. Visit 5 
random areas of the field and count 
beetles on 10 plants in each area. 
Do not pick plants directly adjacent to 
each other. Count the beetles found 
on the tassel, silk, top and bottom of 
leaves, and feeding on the ear tip. 
First, trap beetles in the silk by firmly 
grabbing the silk end of the ear. Count 
beetles on the rest of the plant before 
slowly opening your hand to count 
beetles feeding on the silk and ear tip. 
Western CRW beetle
Northern CRW beetle
Silk clipping
Pollination Protection: Treat corn fields if silks are clipped to 1/2-inch or less 
from the ear and pollination is less than 50% complete. This usually requires 
approximately 5 beetles per plant.
For pollination protection, scout 
fields before 70% of the field has silked. 
Root Protection following corn: Treat if scouting counts from the previous year’s 
egg-laying period reached a field average of 0.75 beetles per plant.
For root protection, scout fields 
during the egg-laying period from 
early August to early September. 
Repeat this scouting procedure on 
7-10 day intervals one or two more 
times during the egg-laying period. 
Root Protection following soybean: Treat corn if yellow sticky trap catches average 
more than 5 Western corn rootworm beetles/trap/day during the egg-laying period 
from early August to early September."""
        },
        {
            "query": "What is the recommended scouting procedure for counting beetles in a corn field?",
            "reference": """how to scout: Count the number of 
CRW beetles on 50 corn plants. Visit 5 
random areas of the field and count 
beetles on 10 plants in each area. 
Do not pick plants directly adjacent to 
each other. Count the beetles found 
on the tassel, silk, top and bottom of 
leaves, and feeding on the ear tip. 
First, trap beetles in the silk by firmly 
grabbing the silk end of the ear. Count 
beetles on the rest of the plant before 
slowly opening your hand to count 
beetles feeding on the silk and ear tip. 
Western CRW beetle
Northern CRW beetle
Silk clipping
Pollination Protection: Treat corn fields if silks are clipped to 1/2-inch or less 
from the ear and pollination is less than 50% complete. This usually requires 
approximately 5 beetles per plant.
For pollination protection, scout 
fields before 70% of the field has silked. 
Root Protection following corn: Treat if scouting counts from the previous year’s 
egg-laying period reached a field average of 0.75 beetles per plant.
For root protection, scout fields 
during the egg-laying period from 
early August to early September. 
Repeat this scouting procedure on 
7-10 day intervals one or two more 
times during the egg-laying period. 
Root Protection following soybean: Treat corn if yellow sticky trap catches average 
more than 5 Western corn rootworm beetles/trap/day during the egg-laying period 
from early August to early September"""
        },
        {
            "query": "During which period should I scout for corn rootworm beetles to ensure root protection, "
                     "and how often should scouting be repeated?",
            "reference": """how to scout: Count the number of 
CRW beetles on 50 corn plants. Visit 5 
random areas of the field and count 
beetles on 10 plants in each area. 
Do not pick plants directly adjacent to 
each other. Count the beetles found 
on the tassel, silk, top and bottom of 
leaves, and feeding on the ear tip. 
First, trap beetles in the silk by firmly 
grabbing the silk end of the ear. Count 
beetles on the rest of the plant before 
slowly opening your hand to count 
beetles feeding on the silk and ear tip. 
Western CRW beetle
Northern CRW beetle
Silk clipping
Pollination Protection: Treat corn fields if silks are clipped to 1/2-inch or less 
from the ear and pollination is less than 50% complete. This usually requires 
approximately 5 beetles per plant.
For pollination protection, scout 
fields before 70% of the field has silked. 
Root Protection following corn: Treat if scouting counts from the previous year’s 
egg-laying period reached a field average of 0.75 beetles per plant.
For root protection, scout fields 
during the egg-laying period from 
early August to early September. 
Repeat this scouting procedure on 
7-10 day intervals one or two more 
times during the egg-laying period. 
Root Protection following soybean: Treat corn if yellow sticky trap catches average 
more than 5 Western corn rootworm beetles/trap/day during the egg-laying period 
from early August to early September"""
        },
        {
            "query": "What factors should I consider when deciding whether to apply insecticides for late-season "
                     "soybean aphid populations",
            "reference": """Managing Late-Season 
Soybean Aphids
Economic Threshold:
Scouting:
250 or more aphids are found 
on 80% of the plants, and aphid 
numbers are rapidly increasing. 
Begin field scouting in late 
June (late vegetative to 
beginning bloom soybean 
growth stages), making one 
or two visits/field/week. 
Management of late-season soybean aphid (SBA) 
populations is complex because of the number of factors 
which influence population growth and potential for 
damage. Give careful consideration to each of these 
factors before deciding on a control recommendation.
This threshold gives ~7 days lead 
time before economic loss is likely 
to occur. Rechecking populations 
of SBA over successive days will 
provide info to determine if 
aphid populations are increasing, 
yet provide sufficient time if an 
insecticide application is required
To calculate a field average, 
count the number of aphids 
on 20-30 plants/field, from 
a sample representative of 
at least 80% of the field.
•  beneficial insects
•  white dwarf soybean aphids
•  signs of aphid diseases
A minimum of two field visits 
are required to determine 
if aphid populations are 
increasing. 
Crop stage: The 250 aphid/plant 
economic threshold is effective 
for the R1-R5 (first flower-full 
pod) development stages."""
        },
        {
            "query": "How should I calculate a field average for soybean aphid populations to make informed "
                     "management decisions",
            "references": """Managing Late-Season 
Soybean Aphids
Economic Threshold:
Scouting:
250 or more aphids are found 
on 80% of the plants, and aphid 
numbers are rapidly increasing. 
Begin field scouting in late 
June (late vegetative to 
beginning bloom soybean 
growth stages), making one 
or two visits/field/week. 
Management of late-season soybean aphid (SBA) 
populations is complex because of the number of factors 
which influence population growth and potential for 
damage. Give careful consideration to each of these 
factors before deciding on a control recommendation.
This threshold gives ~7 days lead 
time before economic loss is likely 
to occur. Rechecking populations 
of SBA over successive days will 
provide info to determine if 
aphid populations are increasing, 
yet provide sufficient time if an 
insecticide application is required
To calculate a field average, 
count the number of aphids 
on 20-30 plants/field, from 
a sample representative of 
at least 80% of the field.
•  beneficial insects
•  white dwarf soybean aphids
•  signs of aphid diseases
A minimum of two field visits 
are required to determine 
if aphid populations are 
increasing. 
Crop stage: The 250 aphid/plant 
economic threshold is effective 
for the R1-R5 (first flower-full 
pod) development stages."""
        },

        {"query": "When do southern corn rootworm larvae typically emerge and begin feeding on corn roots",
         "reference": """Southern corn rootworm 
Scientific names
Diabrotica barberi
Diabrotica virgifera virgifera
Diabrotica undecimpunctata howardi
slopes. Hilltops tend to be a less-
favored egg-laying site.
Eggs begin to develop when
spring soil temperatures reach 50° to
52°F. Larvae emerge and begin
invading corn roots by mid-June,
with the largest number of larvae
usually found in early to mid-July.
Corn rootworms go through three
larval stages (instars) and can move
as much as 20 inches through the soil
during this time. 
Appearance
yellow to green in color and about
the same size as the northern and
western corn rootworm beetles. This
species does not overwinter in
Wisconsin, and is not a threat to corn
produced in the state because it
arrives too late in the summer to
cause damage.
Rootworms—fully grown
larvae—are slender, white worms,
approximately 1⁄2 inch long with
brown to black heads and a dark
plate on the top side of the rear
segment.
Newly hatched larvae (first
instar) feed on the smaller, branching
corn roots. Later instars invade the
inner root tissues that transport
water and needed mineral elements
to the plant. In most instances, larvae
migrate to feed on the newest root
growth. """},
        {"query": "How can you identify fully grown southern corn rootworm larvae and distinguish them "
                  "from other corn rootworm species?",
         "reference": """Southern corn rootworm Scientific names
    Diabrotica barberi
    Diabrotica virgifera virgifera
    Diabrotica undecimpunctata howardi
    slopes. Hilltops tend to be a less-
    favored egg-laying site.
    Eggs begin to develop when
    spring soil temperatures reach 50° to
    52°F. Larvae emerge and begin
    invading corn roots by mid-June,
    with the largest number of larvae
    usually found in early to mid-July.
    Corn rootworms go through three
    larval stages (instars) and can move
    as much as 20 inches through the soil
    during this time. 
    Appearance
    yellow to green in color and about
    the same size as the northern and
    western corn rootworm beetles. This
    species does not overwinter in
    Wisconsin, and is not a threat to corn
    produced in the state because it
    arrives too late in the summer to
    cause damage.
    Rootworms—fully grown
    larvae—are slender, white worms,
    approximately 1⁄2 inch long with
    brown to black heads and a dark
    plate on the top side of the rear
    segment.
    Newly hatched larvae (first
    instar) feed on the smaller, branching
    corn roots. Later instars invade the
    inner root tissues that transport
    water and needed mineral elements
    to the plant. In most instances, larvae
    migrate to feed on the newest root
    growth."""},
        {"query": "What parts of the corn plant do southern corn rootworm larvae target at different stages of their "
                  "development",
         "reference": """Southern corn rootworm 
    Scientific names
    Diabrotica barberi
    Diabrotica virgifera virgifera
    Diabrotica undecimpunctata howardi
    slopes. Hilltops tend to be a less-
    favored egg-laying site.
    Eggs begin to develop when
    spring soil temperatures reach 50° to
    52°F. Larvae emerge and begin
    invading corn roots by mid-June,
    with the largest number of larvae
    usually found in early to mid-July.
    Corn rootworms go through three
    larval stages (instars) and can move
    as much as 20 inches through the soil
    during this time. 
    Appearance
    yellow to green in color and about
    the same size as the northern and
    western corn rootworm beetles. This
    species does not overwinter in
    Wisconsin, and is not a threat to corn
    produced in the state because it
    arrives too late in the summer to
    cause damage.
    Rootworms—fully grown
    larvae—are slender, white worms,
    approximately 1⁄2 inch long with
    brown to black heads and a dark
    plate on the top side of the rear
    segment.
    Newly hatched larvae (first
    instar) feed on the smaller, branching
    corn roots. Later instars invade the
    inner root tissues that transport
    water and needed mineral elements
    to the plant. In most instances, larvae
    migrate to feed on the newest root
    growth."""},

        {"query": "What are the signs of leafminer activity, and why is it important to detect damage early?",
         "reference": """Parasitic wasps can provide a
    limited degree of natural leafmin-
    er control.
    The damage that results from
    leafminer activity may appear as
    blisters, blotchy mines or serpen-
    tine tunnels. Feces of the larvae,
    or frass, can contaminate leafy
    tissue intended for human con-
    sumption. Stunting, due to a
    reduction of photosynthetic leaf
    surface area, can also be a prob-
    lem in vegetable crops not mar-
    keted solely for their foliage.
    Spinach leafminers produce ser-
    pentine mines initially but later
    produce large, undifferentiated
    blotches. Larvae of the vegetable
    leafminer may feed on more than
    one leaf before completing their
    growth.
    It is important to detect leafminer
    damage early before the mar-
    ketability of the crop is affected.
    Efforts to control the insects must
    be started before they enter the
    leaves where they will be hidden
    and protected. Leafminer eggs
    are laid on the lower leaf surface;
    this is the place to check for early
    mining activity.
    Chemical: Because leafminers are
    protected within the plant, insecti-
    cidal control is often difficult. In
    addition, some leafminer popula-
    tions have exhibited resistance to
    organophospate insecticides
    making control difficult. If insecti-
    cides are used, they must be
    applied early in the insect’s life
    cycle to be effective.
    Threshold levels that tell when to
    begin control have not been
    determined for leafminers, but the
    plant’s stage of growth is an
    important factor in determining
    whether to implement control. 
    For pesticide recommedations,
    refer to the UW-Extension publi-
    cation Commercial Vegetable
    Production in Wisconsin (A3422).
    Young plants can withstand less
    damage than older ones. On
    leafy crops such as spinach, let-
    tuce and chard, a 5% threshold
    level is often used.
    Life cycle
    Leafminers overwinter as pupae
    either in the soil or in infested
    plant debris. In spring, adult flies
    emerge and lay eggs on or near
    susceptible hosts. When the
    eggs hatch, the larvae immedi-
    ately begin to enter the leaf and
    mine the mesophyll tissue
    between the upper and lower leaf
    surfaces. When the larvae have
    finished developing, they may
    remain in the plant or drop to the
    ground to pupate. There may be
    several generations of leafminers
    per year; however the first genera-
    tion often does the most damage.
    Control
    Non-chemical: Deep plowing in
    early spring to destroy infested
    weeds and plant material from
    the previous season can reduce
    the severity of leafminer out-
    breaks. Covering susceptible
    crops with floating row covers to
    exclude flies from laying eggs
    may also help. Weed hosts such
    as pigweed, lambsquarters, plan-
    tain, chickweed and nightshade
    should also be destroyed."""},
        {"query": "Why is insecticidal control of leafminers often difficult, and when should insecticides be "
                  "applied for maximum effectiveness",
         "reference": """Parasitic wasps can provide a
    limited degree of natural leafmin-
    er control.
    The damage that results from
    leafminer activity may appear as
    blisters, blotchy mines or serpen-
    tine tunnels. Feces of the larvae,
    or frass, can contaminate leafy
    tissue intended for human con-
    sumption. Stunting, due to a
    reduction of photosynthetic leaf
    surface area, can also be a prob-
    lem in vegetable crops not mar-
    keted solely for their foliage.
    Spinach leafminers produce ser-
    pentine mines initially but later
    produce large, undifferentiated
    blotches. Larvae of the vegetable
    leafminer may feed on more than
    one leaf before completing their
    growth.
    It is important to detect leafminer
    damage early before the mar-
    ketability of the crop is affected.
    Efforts to control the insects must
    be started before they enter the
    leaves where they will be hidden
    and protected. Leafminer eggs
    are laid on the lower leaf surface;
    this is the place to check for early
    mining activity.
    Chemical: Because leafminers are
    protected within the plant, insecti-
    cidal control is often difficult. In
    addition, some leafminer popula-
    tions have exhibited resistance to
    organophospate insecticides
    making control difficult. If insecti-
    cides are used, they must be
    applied early in the insect’s life
    cycle to be effective.
    Threshold levels that tell when to
    begin control have not been
    determined for leafminers, but the
    plant’s stage of growth is an
    important factor in determining
    whether to implement control. 
    For pesticide recommedations,
    refer to the UW-Extension publi-
    cation Commercial Vegetable
    Production in Wisconsin (A3422).
    Young plants can withstand less
    damage than older ones. On
    leafy crops such as spinach, let-
    tuce and chard, a 5% threshold
    level is often used.
    Life cycle
    Leafminers overwinter as pupae
    either in the soil or in infested
    plant debris. In spring, adult flies
    emerge and lay eggs on or near
    susceptible hosts. When the
    eggs hatch, the larvae immedi-
    ately begin to enter the leaf and
    mine the mesophyll tissue
    between the upper and lower leaf
    surfaces. When the larvae have
    finished developing, they may
    remain in the plant or drop to the
    ground to pupate. There may be
    several generations of leafminers
    per year; however the first genera-
    tion often does the most damage.
    Control
    Non-chemical: Deep plowing in
    early spring to destroy infested
    weeds and plant material from
    the previous season can reduce
    the severity of leafminer out-
    breaks. Covering susceptible
    crops with floating row covers to
    exclude flies from laying eggs
    may also help. Weed hosts such
    as pigweed, lambsquarters, plan-
    tain, chickweed and nightshade
    should also be destroyed."""},
        {
            "query": "What non-chemical methods can be used to control leafminer outbreaks and prevent egg-laying by adult flies",
            "reference": """Parasitic wasps can provide a
    limited degree of natural leafmin-
    er control.
    The damage that results from
    leafminer activity may appear as
    blisters, blotchy mines or serpen-
    tine tunnels. Feces of the larvae,
    or frass, can contaminate leafy
    tissue intended for human con-
    sumption. Stunting, due to a
    reduction of photosynthetic leaf
    surface area, can also be a prob-
    lem in vegetable crops not mar-
    keted solely for their foliage.
    Spinach leafminers produce ser-
    pentine mines initially but later
    produce large, undifferentiated
    blotches. Larvae of the vegetable
    leafminer may feed on more than
    one leaf before completing their
    growth.
    It is important to detect leafminer
    damage early before the mar-
    ketability of the crop is affected.
    Efforts to control the insects must
    be started before they enter the
    leaves where they will be hidden
    and protected. Leafminer eggs
    are laid on the lower leaf surface;
    this is the place to check for early
    mining activity.
    Chemical: Because leafminers are
    protected within the plant, insecti-
    cidal control is often difficult. In
    addition, some leafminer popula-
    tions have exhibited resistance to
    organophospate insecticides
    making control difficult. If insecti-
    cides are used, they must be
    applied early in the insect’s life
    cycle to be effective.
    Threshold levels that tell when to
    begin control have not been
    determined for leafminers, but the
    plant’s stage of growth is an
    important factor in determining
    whether to implement control. 
    For pesticide recommedations,
    refer to the UW-Extension publi-
    cation Commercial Vegetable
    Production in Wisconsin (A3422).
    Young plants can withstand less
    damage than older ones. On
    leafy crops such as spinach, let-
    tuce and chard, a 5% threshold
    level is often used.
    Life cycle
    Leafminers overwinter as pupae
    either in the soil or in infested
    plant debris. In spring, adult flies
    emerge and lay eggs on or near
    susceptible hosts. When the
    eggs hatch, the larvae immedi-
    ately begin to enter the leaf and
    mine the mesophyll tissue
    between the upper and lower leaf
    surfaces. When the larvae have
    finished developing, they may
    remain in the plant or drop to the
    ground to pupate. There may be
    several generations of leafminers
    per year; however the first genera-
    tion often does the most damage.
    Control
    Non-chemical: Deep plowing in
    early spring to destroy infested
    weeds and plant material from
    the previous season can reduce
    the severity of leafminer out-
    breaks. Covering susceptible
    crops with floating row covers to
    exclude flies from laying eggs
    may also help. Weed hosts such
    as pigweed, lambsquarters, plan-
    tain, chickweed and nightshade
    should also be destroyed."""},
        {"query": "What are some practices that can help reduce the buildup of smut spores in a field?",
         "reference": """Avoid mechanical injury to 
plants during cultivation. Maintain 
balanced soil fertility and avoid 
excessive nitrogen or manure. Late 
applications of 2,4-D with crop oil, 
which is prohibited on the label. may 
lead to a higher-than-normal inci-
dence of smut galls.
for infection to occur, but is no longer 
needed once the plant has been 
infected. 
Rust The pathogen that causes 
rust requires two hosts to complete its 
life cycle—corn and common yellow 
woodsorrel (Oxalis sp.), a plant that 
grows much farther south. For corn 
grown in the Midwest to be infected, 
spores must be carried from the 
Gulf of Mexico each year on wind 
currents. Tracking the northward 
progression of rust spores is useful in 
determining when the disease poten-
tial is likely to increase. Sweet corn 
plants already infected by the maize 
dwarf mosaic virus are more suscep-
tible to rust infection.
Later-maturing varieties tend to 
have less infection than early vari-
eties. Consult Extension recommen-
dations for locally adapted cultivars. 
Rust Resistance provides the 
primary line of defense against rust 
infections in sweet corn. There are 
numerous rust-resistant sweet corn 
varieties and new ones are released 
every year. For current recommenda-
tions of resistant varieties, consult 
Extension recommendations.
Control
Smut Crop rotation and destruc-
tion of galls before they rupture will 
reduce the buildup of spores in the 
field. Because spores are dissemi-
nated by the wind, crop rotation will 
never be completely effective in pre-
venting this disease."""

         },
        {"query": "What are the primary methods for managing rust infections in sweet corn, and why are resistant "
                  "varieties recommended",
         "reference": """Avoid mechanical injury to 
plants during cultivation. Maintain 
balanced soil fertility and avoid 
excessive nitrogen or manure. Late 
applications of 2,4-D with crop oil, 
which is prohibited on the label. may 
lead to a higher-than-normal inci-
dence of smut galls.
for infection to occur, but is no longer 
needed once the plant has been 
infected. 
Rust The pathogen that causes 
rust requires two hosts to complete its 
life cycle—corn and common yellow 
woodsorrel (Oxalis sp.), a plant that 
grows much farther south. For corn 
grown in the Midwest to be infected, 
spores must be carried from the 
Gulf of Mexico each year on wind 
currents. Tracking the northward 
progression of rust spores is useful in 
determining when the disease poten-
tial is likely to increase. Sweet corn 
plants already infected by the maize 
dwarf mosaic virus are more suscep-
tible to rust infection.
Later-maturing varieties tend to 
have less infection than early vari-
eties. Consult Extension recommen-
dations for locally adapted cultivars. 
Rust Resistance provides the 
primary line of defense against rust 
infections in sweet corn. There are 
numerous rust-resistant sweet corn 
varieties and new ones are released 
every year. For current recommenda-
tions of resistant varieties, consult 
Extension recommendations.
Control
Smut Crop rotation and destruc-
tion of galls before they rupture will 
reduce the buildup of spores in the 
field. Because spores are dissemi-
nated by the wind, crop rotation will 
never be completely effective in pre-
venting this disease."""

         },
        {"query": "Why are sweet corn plants infected with maize dwarf mosaic virus more susceptible to rust infections",
         "reference": """Avoid mechanical injury to 
plants during cultivation. Maintain 
balanced soil fertility and avoid 
excessive nitrogen or manure. Late 
applications of 2,4-D with crop oil, 
which is prohibited on the label. may 
lead to a higher-than-normal inci-
dence of smut galls.
for infection to occur, but is no longer 
needed once the plant has been 
infected. 
Rust The pathogen that causes 
rust requires two hosts to complete its 
life cycle—corn and common yellow 
woodsorrel (Oxalis sp.), a plant that 
grows much farther south. For corn 
grown in the Midwest to be infected, 
spores must be carried from the 
Gulf of Mexico each year on wind 
currents. Tracking the northward 
progression of rust spores is useful in 
determining when the disease poten-
tial is likely to increase. Sweet corn 
plants already infected by the maize 
dwarf mosaic virus are more suscep-
tible to rust infection.
Later-maturing varieties tend to 
have less infection than early vari-
eties. Consult Extension recommen-
dations for locally adapted cultivars. 
Rust Resistance provides the 
primary line of defense against rust 
infections in sweet corn. There are 
numerous rust-resistant sweet corn 
varieties and new ones are released 
every year. For current recommenda-
tions of resistant varieties, consult 
Extension recommendations.
Control
Smut Crop rotation and destruc-
tion of galls before they rupture will 
reduce the buildup of spores in the 
field. Because spores are dissemi-
nated by the wind, crop rotation will 
never be completely effective in pre-
venting this disease."""

         },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  },
        # {"query": "",
        #  "reference": """"""
        #
        #  }

    ]

asyncio.run(run_comparison(test_cases=test_cases, tags=tags))
