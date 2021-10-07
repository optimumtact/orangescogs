# Standard Imports
import random

# Discord Imports
import discord

# Redbot Imports
from redbot.core import commands

__version__ = "1.2.1"
__author__ = "oranges"

BaseCog = getattr(commands, "Cog", object)


class Pets(BaseCog):
    def __init__(self, bot):
        self.bot = bot
        self.breakfast = [
            "Baked Shrimp Scampi",
            "Strawberries Romanov (La Madeleine copycat)",
            "Tomato Basil Soup (La Madeleine copycat)",
            "John Thorne's Pecan Pie",
            "Smoked Salmon Ebelskivers",
            "Godiva Angel Pie",
            "Spaetzle",
            "Pot Roast Carbonnade",
            "Old Fashion Vegetable Soup",
            "Onion Pie",
            "Godiva Dark Chocolate Cheesecake",
            "Greek Salad",
            "Flaky Buttermilk Biscuits",
            "Grilled Portobello Mushrooms Stacked with Fresh Spinach and Shaved Manchego Cheese",
            "Sherry Vinaigrette",
            "Margherita Salad",
            "Mexican Ensalada",
            "Guacamole",
            "Sweet Almond Date Smoothie",
            "Super Protein Salad",
            "The Shake",
            "Apple Carrot Salad",
            "Extreme Green Salad",
            "Berry Sauce",
            "Popeye's Muscle Salad",
            "Breakfast Mediterranean Scramble",
            "Best Oatmeal Ever",
            "Lovely Lentils",
            "Sweet Mashed Potatoes",
            "Steakhouse steaks",
            "Roquefort Cheese Sauce",
            "Stove top mac and cheese",
            "The Original Chex Party Mix",
            "Handmade Pasta",
            "Emeril Essence Creole Seasoning",
            "Vegetarian Chili",
            "Basil-Lime Vinaigrette",
            "Lentil Soup",
            "Natural sports drink",
            "Vegetable Stock",
            "Grilled garlic-lime fish tacos",
            "Spicy Rice Casserole",
            "Citrus Rice Salad",
            "Straw and Hay Fettuccine Tangle",
            "Green-packed Stir Fry with Fresh Herbs",
            "Apple-Brie Panini",
            "Shredded Green Beans",
            "Hot Cocoa",
            "Pesto Orzo with Peas",
            "Roasted potatoes and tomatoes",
            "Almond Caesar salad with croutons",
            "Spiced Apple Sauce",
            "Schnitzel",
            "Oregano Marinated Chicken",
            "Black bean and cheese tacos",
            "Joan's Broccoli Madness",
            "Marinara Sauce",
            "Creamy tomato soup",
            "Triple Grilled Cheese",
            "Vegetarian Steamed Dumplings",
            "Soba salad with asparagus and shrimp",
            "Tofu and Sweet Potato Jambalaya",
            "Parker's split pea soup",
            "Wild Mushroom Risotto",
            "Roasted Salmon with Walnut-Pepper Relish",
            "Brown rice, chickpea, feta, and mint salad",
            "Greek yogurt with homemade honeycomb",
            "Cocktail Sauce",
            "Heinz Chili Sauce",
            "Spinach souffle",
            "Roasted Shallot Vinaigrette",
            "Peanut Noodle Salad",
            "Artichoke, Leek, and Potato Casserole",
            "Broccoli with Parmesan and Walnuts",
            "Emeril's strawberry lemonade",
            "Pizza bianca",
            "Smoky Sweet-Potato Soup",
            "Green goddess dressing",
            "Creamy roasted garlic dressing",
            "Creamy ranch dressing",
            "Creamy blue cheese dressing",
            "Creamy peppercorn-Parmesan dressing",
            "Cherry-lime cups",
            "Roasted salsa",
            "Shrimp and edamame with lime",
            "Strawberries and cream bars",
            "No-churn vanilla ice cream",
            "Frozen chocolate mousse trifles",
            "Frozen lemon souffle",
            "Coconut lime semifreddo",
            "Sweet cherry granita",
            "Raspberry-lemon thumbprint cookies",
            "Glazed carrots",
            "Baby Brussels sprouts with wild rice and pecans",
            "Pumpkin mousse",
            "Salted caramel six layer chocolate cake",
            "Cranberry almond muffins",
            "Hazelnut pear muffins",
            "Hazelnut pastry dough",
            "Pesto",
            "Pate brisee",
            "Tex-mex rice and black eyed peas",
            "Baked eggs and beans on toast",
            "Warm shrimp and potato salad",
            "Cherry couscous pudding",
            "Spinach lasagna with mushroom ragu",
            "Chocolate chestnut mousse",
            "Spicy sauteed kale with lemon",
            "Caesar Salad Dressing",
            "Melomakarona - Honey Cookies with Walnuts",
            "Kalitsounia Kritis: Sweet Cheese Pastries from Crete",
            "Gluten-free chocolate chips cookies",
            "Homemade candy canes",
            "Pecan Pie",
            "Asian Salad",
            "Pasta with roasted vegetables and bacon",
            "Pretzel shortbread bar",
            "Simple syrup",
            "Hot and nutty whiskey sours",
            "Three cheese macaroni",
            "Broken glass cupcakes",
            "Homemade beef stock",
            "French onion soup",
            "Red lentil soup with sage and bacon",
            "Green pea soup with cheddar scallion panini",
            "Broccoli soup with cheddar toasts",
            "Coconut shrimp soup",
            "Creamy caramelized onion soup",
            "Hearty spinach and chickpea soup",
            "Chervil cream",
            "Mushroom soup",
            "Harvest pumpkin soup",
            "Lighter macaroni and cheese",
            "Chocolate cheesecake squares",
            "Chocolate cinnamon pudding",
            "Creepy crawly cake",
            "Blood orange cocktails",
            "Japanese style grilled salmon",
            "Dang cold Asian noodle salad",
            "Grilled salmon gyros",
            "Homemade ponzu sauce",
            "Sushi rice",
            "Grilled salmon sushi rice bowl",
            "Roasted cauliflower and white beans",
            "Shrimp and cabbage stir fry",
            "Avocado feta dip",
            "Herb crusted salmon with spinach salad",
            "Chocolate-Hazelnut Icebox Cake",
            "Smoky Yukon Gold Potato Chowder",
            "Orecchiette with roasted cauliflower",
            "Salsa fresca",
            "Black bean salad with chipotle honey dressing",
            "Linguine with asparagus and egg",
            "Spanakopita",
            "Coffee, hazelnut, and banana granola",
            "Cherry lime granola",
            "Creamy artichoke dip",
            "Simple lemon cake",
            "Gooey layered everything bars",
            "Chili Lemon Cauliflower",
            "Pecan molasses granola",
            "Salmon and potatoes in tomato sauce",
            "Pear and chocolate brioche bread pudding",
            "Potato hash with spinach and eggs",
            "Brussels sprouts with maple and cayenne",
            "Roasted sweet potatoes and bacon",
            "Salted chocolate milk",
            "Marinated feta, spinach & poached egg salad",
            "Drop biscuits (Cook's Illustrated)",
            "Light ranch dressing",
            "Light Italian dressing",
            "Chocolate banana ice cream pie",
            "Salmon rillettes with tomato salad",
            "Granitaville",
            "Pickled red onions",
            "Red sangria",
            "Smoky white bean and arugula panini",
            "Easy chickpea and vegetable curry",
            "White sangria",
            "Rose sangria",
            "Chiles Rellenos",
            "Hawaiian style short ribs (slow cooker)",
            "Cheese crackers",
            "Roasted sweet potato salsa",
            "Shredded Brussels sprouts with pancetta",
            "Maple brown butter semifreddo",
            "Brown sugar buttermilk pie",
            "Baked Beans",
            "Lemonade",
            "Mushroom and lentil soup",
            "Apple brandy brown betty",
            "Pumpkin chocolate whoopie pies",
            "Indian Chickpea Wrap",
            "Veggie burger pockets",
            "Towering flourless chocolate cake",
            "Lemon white chocolate cookies",
            "Chocolate babka",
            "Chocolate ice cubes",
            "French-Onion Stuffed Potatoes",
            "Kale Salad with Marcona Almonds and Sherry Vinaigrette",
            "Ghirardelli Ultimate Double Chocolate Cookies",
            "Squash lasagna with fresh basil",
            "Brazilian sweet bread",
            "Chocolate dipped coconut macaroons",
            "Peppermint crunch bark",
            "Mexican wedding cookies",
            "Kale caesar salad",
            "Kale and feta salad",
            "Eggnog glazed spritz cookies",
            "Taco Spread",
            "Tex Mex Scones",
            "Mocha chip cookie scones",
            "Scalloped Yukon Gold and Sweet Potato Gratin",
            "Soba Noodle Salad",
            "Antipasto Chef's Salad",
            "Chipotle honey vinaigrette",
            "Asparagus and lemon risotto",
            "Moroccan lentil salad",
            "Tuscan panzanella salad",
            "PB&J smoothie",
            "Stir-Fry Sauce (Hoisin and Lime)",
            "Stir-Fry Sauce (Spicy)",
            "Stir-Fry Sauce (Sweet and Sour)",
            "Stir-Fry Sauce (Clear)",
            "Veggie Pizza",
            "Eggs",
            "Goat cheese, sun dried tomato, and pesto torta",
            "Frozen Dinner",
            "Vineyard tofu salad",
            "Tempeh sauerbraten",
            "Bavarian kartofflepuffer (potato pancakes)",
            "Cheddar beer soup",
            "Kale panzanella",
            "Salmon Tuscano with Herbed Orzo",
            "Pecan-Crusted Mozzarella Salad",
            "Tomato-Basil Soup with Ricotta Dumplings",
            "Tomato, Basil and Portobello Napoleons",
            "Creamy Broccoli & Sun-Dried Tomato Orzotto",
            "Slow-Cooker Greek Stuffed Peppers",
            "Mixed Tomato Cobbler with Gruyere Crust",
            "Gnocchi",
            "Grilled Cheese & Tomato Skillet",
            "Mediterranean Patio Pizza",
            "Baked Ziti with Crunchy Italian Salad and Garlic Bread",
            "Millet bread (Corn-free cornbread)",
            "Chocolate-Pumpkin Cheesecake Bars",
            "Shortbread cookies with salted caramel",
            "Vanilla chocolate sandwich cookies",
            "Jamie's Old-Fashioned Ginger Crinkle Cookies",
            "Baked Penne with Roasted Vegetables",
            "All-day minestrone (slow cooker)",
            "Berry Granola Parfait",
            "Golden Granola",
            "Smoked salmon baked potatoes",
            "Guacamole baked potatoes",
            "Bruschetta baked potatoes",
            "Samosa baked potatoes",
            "Apple-cheddar baked sweet potatoes",
            "Paella pasta salad",
            "Shrimp fried rice",
            "Ina Garten's Pesto",
            "Pinto bean and poblano tacos",
            "Muttar paneer",
            "Almost famous broccoli cheddar soup",
            "Tofu parmesan subs",
            "Pasta with escarole",
            "Squash and bean burritos",
            "Broiled halibut with ricotta-pea puree",
            "Veggie Carribean Panini",
            "Italian ice",
            "Baja fish tacos",
            "Seven layer bars",
            "Ranch dip with vegetables",
            "Classic cheese fondue (for Cuisinart Fondue Pot)",
            "Miso dressing",
            "Baked eggs and grits",
            "Open face egg and tomato sandwich",
            "Lemony walnut chickpea salad with goat's cheese",
            "Buttery shrimp and radish pasta",
            "Skillet shrimp and orzo",
            "Salad with Radishes and Spicy Pumpkin Seeds",
            "Stuffed poblanos",
            "Black bean and brown rice cakes",
            "Hot Nutty Irishman",
            "English muffin with apple and cheddar",
            "Penne with Butternut Squash and Goat Cheese",
            "Couscous stuffed bellpeppers with basil sauce",
            "Chopped antipasto salad",
            "Salad with egg, nuts, and veggies",
            "Spider web brownies",
            "Fudge brownies",
            "Almond cloud cookies",
            "Double-shot mocha chunks",
            "Peanut butter-oatmeal sandwich cookies",
            "Bagel and lox deviled eggs",
            "Mayonnaise",
            "Pesto millet grits with tomato ragout",
            "Spicy orange tofu and vegetable stir-fry",
            "Coconut shrimp with tropical rice",
            "Chipotle black-eyed pea salad",
            "Greek layered dip with pita chips",
            "Butternut squash chili",
            "Rosemary mushroom chickpea ragout",
            "Sauteed Mushrooms with Toasted Flatbread and Baked Eggs",
            "Shakshuka with chickpeas",
            "Eggplant meatballs with marinara",
            "Sweet potato millet burgers",
            "Arroz non pollo (slow cooker)",
            "Flan",
            "Homemade pecan and maple nut butter",
            "Mini Tostadas",
            "Caprese Skewers",
            "Artichoke Risotto with Mascarpone, Lemon, and Thyme",
            "Herbed biscuits with smoked salmon",
            "French Onion Dip",
            "Thai Vegetable Stir-fry",
            "Mediterranean Grain Salad",
            "Cannoli",
            "Fudge drops (cookies)",
            "Easy florentines",
            "Simple candied orange peel",
            "Maple shortbread sandwich cookies",
            "Pecan squares",
            "Fruity oatmeal topping",
            "Arugula Salad with Figs, Prosciutto, Walnuts, and Parmesan",
            "Red Lentil Soup with North African Spices",
            "Eggplant involtini",
            "Texas chili potato skins",
            "Maple-bacon potato skins",
            "Frisco gourmet potato skins",
            "Toasted ravioli potato skins",
            "Vegetable and tofu pad thai",
            "Wasabi Salmon with Miso-Sesame Sauce",
            "Cabbage-Asparagus Salad with Tahini Dressing",
            "Microwave mug brownie",
            "Egg sauce",
            "Black-eyed pea burgers with summer squash slaw",
            "Korean scallion pancakes with vegetable salad",
            "Sweet and sour wheatballs",
            "Baked tofu",
            "Southwestern brown rice bowl",
            "Sweet, Spicy & Salty Candied Pecans",
            "Crunchy quinoa cutlets with fresh tomato salsa",
            "Panko-crusted tofu with black bean salad",
            "Farro Fagioli Minestrone",
            "Spanish frittata with mixed greens salad",
            "Roasted root vegetables with creamy grits",
            "Farmer's market vegetable pot pie",
            "Eggplant parmesan pizza",
            "Grilled cheese and romesco sandwiches",
            "Barley risotto verde",
            "French onion potato tart",
            "Perfect soft cooked egg",
            "Poblano, mushroom and potato tacos",
            "Tofu Cuban sandwiches",
            "Wild mushroom and cauliflower lasagna",
            "Hot cereal with apple butter and walnuts",
            "Mexican potato omelet",
            "Caramelized onion and brie pizza",
            "Gazpacho Soup",
            "Eggs with mushrooms and tomatoes",
            "Fruit and cheese breakfast",
            "Morning pizza",
            "Mustard, Avocado, and Dill on a Whole-Wheat Muffin With Boiled Egg",
            "Miso salad dressing",
            "Miso soup",
            "Charred Eggplant and Walnut Pesto Pasta Salad",
            "Baked English Muffins",
            "Mesquite chocolate chip cookies",
            "Asparagus pesto",
            "Savory Oatmeal and Soft-Cooked Egg",
            "Goat cheese Nicoise",
            "Oatmeal-crusted trout",
            "Bourbon praline cake",
            "Salmon Burgers with Caesar Slaw",
            "Tapenade",
            "Leek Salad with Grilled Haloumi Cheese and Wheat Berries",
            "Hoisin-Lime Salmon with Asparagus Couscous",
            "Salmon Nicoise Salad",
            "Baked Gnocchi with Prosciutto & Spinach",
            "Shrimp Scampi with Pasta",
            "Adult Lunchable with Veggies, Salami, and Boursin",
            "Seitan and three-color pepper stir-fry bento",
            "Tamagoyaki Bento",
            "Less-mess oven bacon",
            "Chocolate chip pumpkin bread",
            "The best angel food cake",
            "Breaded and fried shrimps",
            "Carrot and celeriac (celery root) salad",
            "Spring Chickpea Pasta Salad",
            "Carrot kinpira",
            "Salt block cucumber salad",
            "Salt-baked walnut brioche scones",
            "Hot buttered rum",
            "Overnight Cinnamon Rolls",
            "Sweet pepper and onion confit",
            "Basic bento: tofu and egg",
            "Petite vegetable frittatas",
            "Couscous Salad with Roasted Vegetables and Chickpeas",
            "Roasted Shrimp, Endive, and Red Onion Salad",
            "Udon noodle soup",
            "Oaxaca Cheese & Plantain Tortas with Tangelo & Radish Salad",
            "Restaurant Style Butter Chicken in Slow Cooker",
            "Mushroom & Broccoli Casserole with Baked Pastry",
            "Penne & Arrabbiata Sauce with Roasted Carrot & Tangelo Salad",
            "Smoky Seared Cod with Roasted Potatoes & Dates",
            "Kale & White Cheddar Quesadillas with Radishes & Fried Eggs",
            "Almond latte overnight oats",
            "French toast popcorn seasoning",
            "Baked Tofu Banh Mi Salad",
            "Mexican caprese salad",
            "Chocolate covered strawberry quick oatmeal",
            "Golden-crusted Brussels sprouts",
            "Bacon cheddar chive scones",
            "Sweet and Spicy Tofu with Jasmine Rice and Crispy Shallot",
            "Olive and Pepper Grilled Cheese Sandwiches",
            "Mediterranean Salad with Artichokes, Penne, and Sun-Dried Tomatoes",
            "Tofu katsu onigirazu",
            "Super veggie onigirazu",
            "Hummus vegetable sandwich",
            "Oregano halloumi with orzo salad",
            "Aged Eggnog",
            "Cucumber, Avocado, and Miso Spinach Rice Bowl",
            "Spicy poblano pepper and cheese tortas",
            "Chirashi-Style Rice Bowls",
            "Sweet & Savory Korean Rice Cakes",
            "Roasted Brussels sprouts and freekeh salad",
            "Salsa Scramble",
            "Cheesy mushroom omelette",
            "Black Forest Bircher",
            "Eggs baked in avocados",
            "Almond muffin in a minute",
            "Flaxseed muffin in a minute",
            "44-Clove Garlic Soup",
            "Pesto Cavatelli w/ Mushrooms and Spicy Breadcrumbs",
            "Black bean mini burgers",
            "Mini hamburger bento (Select a mini burger recipe too)",
            "Fresh salmon mini burgers",
            "Avocado, olive tapenade, and chedder toast",
            "Cozy bean and egg skillet for two",
            "Whipped eggs on toast",
            "Peach & Pickled Pepper Grilled Cheese",
            "Black bean and zucchini enchiladas",
            "Mexican spice blend",
            "Vietnamese-Style Vegetable Sandwiches with Spicy Mayo and Roasted Broccoli",
            "Roasted Sweet Potato Quesadillas",
            "Vadouvan curry spice blend",
            "Niçoise-Style Salad  with Fingerling Potatoes, Summer Squash, & Fried Eggs",
            "Mulled cranberry apple cider",
            "Creamy chipotle salad dressing",
            "Baked macaroni and cheese",
            "Cavatelli and kale with fried rosemary and walnuts",
            "Falafel with Spicy Feta Sauce and Vegetable Salad",
            "Spicy salmon onigirazu",
            "Malted hot cocoa",
            "Miso-ginger dressing",
            "Pizza dough",
            "Spicy black bean quesadillas with roasted carrot and avocado salad",
            "Leftover BonChon Salad",
            "Vadouvan-spiced vegetable fritters with salad",
            "Vanilla Cupcakes",
            "Chocolate Cupcakes",
            "Pickled Beet & Hard-Boiled Egg Sandwiches with Smoky Mayonnaise",
            "Butternut Squash & Fontina Calzones with Apple & Arugula Salad",
            "Mushroom Barley Soup",
            "Egg, cucumber, and smoked gouda spread sandwiches",
            "Miso sweet potato donburi",
            "Tofu soboro (iridofu)",
            "Egg soboro (iritamago)",
            "Tofu soboro bento",
            "Carrot soboro",
            "Spiced Cod & Summer Squash Cakes",
            "Cajun Catfish and Spiced Rice",
            "Indian-style paneer and creamy tomato curry",
            "Tonkatsu sauce",
            "Gluten-Free Chocolate-Tahini Brownies",
            "Eggs on Toast",
            "Beans and garlic toast in broth",
            "Smoky Brussels Sprouts & Black Bean Tacos",
            "Japanese egg salad sandwich (tamago sando)",
            "Kaeshi",
            "Soba Noodle Bento",
            "Peanut Butter Oatmeal Breakfast Cookies",
            "Scallops over Truffled Mushroom Risotto",
            "Snickerdoodle mug cake",
            "Dark chocolate raspberry breakfast bake",
            "Oatmeal cookie dough breakfast bake",
            "Spicy poblano and mushroom quesadillas",
            "Ranch Dressing Dry Mix",
            "Ranch Dressing",
            "Fontina, Persimmon, and Onion Grilled Cheese",
        ]
        self.coffee = [
            "Affogato",
            "Americano",
            "Caffè Latte",
            "Caffè Mocha",
            "Cafè Au Lait",
            "Cappuccino",
            "Double Espresso (doppio)",
            "Espresso",
            "Espresso Con Panna",
            "Espresso Macchiato",
            "Flat White",
            "Frappé",
            "Freakshake",
            "Irish Coffee",
            "Latte Macchiato",
            "Lungo",
            "Ristretto",
        ]
        self.ethical_alternatives = [
            "Soy",
            "Oat",
            "Almond",
        ]
        self.temps = ["n iced", " steaming hot", " disappointingly lukewarm"]

        self.quotes = [
            "My vision is augmented.",
            "Well, since that makes you my new boss, take a long look at Manderley's dead body. Consider that my resignation; I don't have time to write a letter.",
            "When due process fails us, we really do live in a world of terror.",
            "You mechs may have copper wiring to reroute your fear of pain, but I've got nerves of steel.",
            "I never had time to take the Oath of Service to the Coalition. How about this one? I swear not to rest until UNATCO is free of you and the other crooked bureaucrats who have perverted its mission.",
            "Call me nostalgic, but the nightlife seems to have lost its old charm.",
            "Some gang-banger, maybe you should think about going back to school.",
            "Bravery is not a function of firepower.",
            "Human beings may not be perfect, but a computer program with language synthesis is hardly the answer to the world's problems.",
            "Every war is the result of a difference of opinion. Maybe the biggest questions can only be answered by the greatest of conflicts."
            "What good's an honest soldier if he can be ordered to behave like a terrorist?",
            "You've got ten seconds to beat it before I add you to the list of NSF casualties.",
            "What a shame.",
            "A forgotten virtue like honesty is worth at least twenty credits.",
            "I'm not big into books.",
            "I'm not going to stand here and listen to you badmouth the greatest democracy the world has ever known.",
            "Maybe you should get a job",
            "Number one: that's terror",
            "I can't spare any arms right now. Please retreat to a safe location.",
            "A BOMB?!",
            "What a shame.",
            "Do you have a single fact to back that up?",
            "You might as well tell me the rest. If I'm gonna kill you, you're already dead.",
            "Sticks and stones...",
            "The crossbow. Sometimes you've got to make a silent takedown.",
        ]
        self.undies = {
            1:"aren't wearing any at all :flushed:",
            97.9:"have some utilitarian work day ones on",
            1:"have some lacey risque ones!!!!",
            0.1:"...wait, wh-a-a...whats that liquid?"
        }

        self.push_attempts = ["pushes", "violently shoves", "playfully pushes", "tries and fails to push", "falls over trying to push"]

    @commands.command()
    async def pet(self, ctx, *, name: str):
        """
        Pet a user
        """
        await ctx.send(
            "*{} pets {} gently on the head*".format(ctx.author.mention, name)
        )

    @commands.command(aliases=["tailpull"])
    async def pull(self, ctx, *, name: str):
        """
        Tail pulling
        """
        await ctx.send("*pulls {}'s tail*".format(name))

    @commands.command()
    async def bite(self, ctx, *, name: str):
        """
        Nom
        """
        await ctx.send(
            "*{} bites {}'s tail softly, nom*".format(ctx.author.mention, name)
        )

    @commands.command()
    async def tailbite(self, ctx, *, name: str):
        """
        Nom
        """
        await ctx.send(
            "*{} bites {}'s tail ferociously and tears it off completely*".format(
                ctx.author.mention, name
            )
        )

    @commands.command(aliases=["taildestroy"])
    async def destroy(self, ctx, *, name: str):
        """
        Ouch
        """
        await ctx.send(
            "*{} picks up {} and spins them like a whirlwind, their tail is ripped off and they fly away in an arc*".format(
                ctx.author.mention, name
            )
        )

    @commands.command(aliases=["tailbrush"])
    async def brush(self, ctx, *, name: str):
        """
        Tail brushing
        """
        await ctx.send("*brushes {}'s tail gently*".format(name))

    @commands.command()
    async def coffee(self, ctx, *, name: str):
        """
        Give a user a nice coffee
        """
        await ctx.send(
            "*{} serves {} a{} {}*".format(
                ctx.author.mention,
                name,
                random.choice(self.temps),
                random.choice(self.coffee),
            )
        )

    @commands.command()
    async def throw(self, ctx, *, name: str):
        """
        Throw a coffee at someone
        """
        await ctx.send(
            "*{} makes a{} {} and then picks it up and fucking hurls it at {}'s face*".format(
                ctx.author.mention,
                random.choice(self.temps),
                random.choice(self.coffee),
                name,
            )
        )

    @commands.command()
    async def sticky(self, ctx, *, name: str):
        """
        Give a user a smugly superior sense of self worth
        """
        milk =  random.choice(self.ethical_alternatives)
        if random.randrange(100) < 1:
            milk = 'breast'
        await ctx.send(
            "*{} serves {} a{} {} with {} milk. How ethical! Is that a hint of smug superiority on the face of {}?*".format(
                ctx.author.mention,
                name,
                random.choice(self.temps),
                random.choice(self.coffee),
                milk,
                name,
            )
        )

    @commands.command()
    async def ruffle(self, ctx, *, name: str):
        """
        Ruffle their hair
        """
        await ctx.send(
            "*{} ruffles {}'s hair gently, mussing it up a little*".format(
                ctx.author.mention, name
            )
        )

    @commands.command()
    async def bap(self, ctx, *, name: str):
        """
        Bap!!!
        """
        await ctx.send("*{} baps {} on the head*".format(ctx.author.mention, name))
    
    @commands.command()
    async def slap(self, ctx, *, name: str):
        await ctx.send("*{} slaps {} in the face*".format(ctx.author.mention, name))
    
    @commands.command()
    async def hug(self, ctx, *, name: str):
        """
        hug, awww!!!
        """
        await ctx.send(
            "*{} gathers {} up in their arms and wraps them in a warm hug*".format(
                ctx.author.mention, name
            )
        )

    @commands.command()
    async def fine(self, ctx, *, name: str):
        """
        You so, fucking FINE
        """
        await ctx.send(
            "{} you are fined one credit for violation of the textual morality statutes".format(
                name
            )
        )

    @commands.command()
    async def denton(self, ctx, *, name: str = None):
        """
        JC, A BOMB
        """
        if name:
            message = f"{name}: {random.choice(self.quotes)}"
        else:
            message = f"{random.choice(self.quotes)}"

        await ctx.send(message)

    @commands.command(aliases=["entwine"])
    async def tailentwine(self, ctx, *, name: str):
        """
        Cat!
        """
        await ctx.send(
            "*{} wraps their tail around {}'s tail*".format(ctx.author.mention, name)
        )
    
    @commands.command(aliases=["food"])
    async def breakfast(self, ctx, *, name: str):
        """
        Yum
        """
        items = random.sample(self.breakfast, 3)
        await ctx.send(
            "{} serves {} a plate of {} and {}, Yummy!".format(ctx.author.mention, name, ', '.join(items[0:2]), items[2])
        )
        
    @commands.command()
    async def push(self, ctx, *, name: str):
        """
        *pushes u*
        """
        await ctx.send(
            "*{} {} {} over!*".format(
                ctx.author.mention, random.choice(self.push_attempts), name
            )
        )

    @commands.command()
    async def checkundies(self, ctx, *, name: str):
        """
        *Checks your undies*
        """
        await ctx.send(
            "*{} checks if {} is wearing undies, wow it looks like they {}*".format(
                ctx.author.mention, name, random.choices(list(self.undies.values()), list(self.undies.keys()))[0]
            )
        )

    @commands.command()
    async def setspouse(self, ctx, *, name: str):
        """
        *becomes your bf*
        """
        await ctx.send(
            "{} sets {} as their spouse! How cute.".format(
                ctx.author.mention, name
            )
        )
