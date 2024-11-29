# Copyright 2024 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"HIGGS through FLUTE (Flexible Lookup Table Engine for LUT-quantized LLMs) integration file"

from math import sqrt

from ..utils import (
    is_flute_available,
    is_hadamard_available,
    is_torch_available,
)


if is_torch_available():
    import torch
    from torch import nn


if is_flute_available():
    import flute.utils

if is_hadamard_available():
    from fast_hadamard_transform import hadamard_transform

if is_flute_available():
    import flute.utils
    from flute.integrations.higgs import prepare_data_transposed


def pad_to_block(tensor, dims, had_block_size, value=0):
    pad_dims = [0 for _ in range(2 * len(tensor.shape))]
    for dim in dims:
        size = tensor.shape[dim]
        next_multiple_of_1024 = ((size - 1) // had_block_size + 1) * had_block_size
        delta = next_multiple_of_1024 - size
        pad_dims[-2 * dim - 1] = delta

    return nn.functional.pad(tensor, pad_dims, "constant", value)


def get_higgs_grid(p: int, n: int):
    if (p, n) == (2, 256):
        return torch.tensor(
            [
                [-2.501467704772949, 0.17954708635807037],
                [-0.6761789321899414, 1.2728623151779175],
                [-1.8025816679000854, 0.7613157629966736],
                [-0.538287878036499, -2.6028504371643066],
                [0.8415029644966125, -0.8600977659225464],
                [0.7023013234138489, 3.3138747215270996],
                [0.5699077844619751, 2.5782253742218018],
                [3.292393207550049, -0.6016128063201904],
                [0.5561617016792297, -1.7723814249038696],
                [-2.1012380123138428, 0.020958125591278076],
                [0.46085724234580994, 0.8428705334663391],
                [1.4548040628433228, -0.6156039237976074],
                [3.210029363632202, 0.3546904921531677],
                [0.8893890976905823, -0.5967988967895508],
                [0.8618854284286499, -3.2061192989349365],
                [1.1360996961593628, -0.23852407932281494],
                [1.6646337509155273, -0.9265465140342712],
                [1.4767773151397705, 1.2476022243499756],
                [-1.0511897802352905, 1.94503915309906],
                [-1.56318998336792, -0.3264186680316925],
                [-0.1829211413860321, 0.2922491431236267],
                [-0.8950616717338562, -1.3887052536010742],
                [-0.08206957578659058, -1.329533576965332],
                [-0.487422913312912, 1.4817842245101929],
                [-1.6769757270812988, -2.8269758224487305],
                [-1.5057679414749146, 1.8905963897705078],
                [1.8335362672805786, 1.0515104532241821],
                [0.3273945450782776, 1.0491033792495728],
                [-3.295924186706543, -0.7021600008010864],
                [-1.8428784608840942, -1.2315762042999268],
                [-0.8575026392936707, -1.7005949020385742],
                [-1.120667815208435, 0.6467998027801514],
                [-0.1588846743106842, -1.804071068763733],
                [-0.8539647459983826, 0.5645008683204651],
                [-1.4192019701004028, -0.6175029873847961],
                [1.0799058675765991, 1.7871345281600952],
                [1.171311855316162, 0.7511613965034485],
                [2.162078380584717, 0.8044339418411255],
                [1.3969420194625854, -1.243762493133545],
                [-0.23818807303905487, 0.053944624960422516],
                [2.304199457168579, -1.2667627334594727],
                [1.4225027561187744, 0.568610668182373],
                [0.376836895942688, -0.7134661674499512],
                [2.0404467582702637, 0.4087389409542084],
                [0.7639489769935608, -1.1367933750152588],
                [0.3622530400753021, -1.4827953577041626],
                [0.4100743532180786, 0.36108437180519104],
                [-1.5867475271224976, -1.618212342262268],
                [-2.2769672870635986, -1.2132309675216675],
                [0.9184022545814514, -0.34428009390830994],
                [-0.3902314603328705, 0.21785245835781097],
                [3.120687484741211, 1.3077973127365112],
                [1.587440848350525, -1.6506884098052979],
                [-1.718808889389038, -0.038405973464250565],
                [-0.6888407468795776, -0.8402308821678162],
                [-0.7981445789337158, -1.1117373704910278],
                [-2.4124443531036377, 1.3419722318649292],
                [-0.6611530184745789, 0.9939885139465332],
                [-0.33103418350219727, -0.16702833771705627],
                [-2.4091389179229736, -2.326857566833496],
                [1.6610108613967896, -2.159703254699707],
                [0.014884627424180508, 0.3887578248977661],
                [0.029668325558304787, 1.8786455392837524],
                [1.180362582206726, 2.699317216873169],
                [1.821286678314209, -0.5960053205490112],
                [-0.44835323095321655, 3.327436685562134],
                [-0.3714401423931122, -2.1466753482818604],
                [-1.1103475093841553, -2.4536871910095215],
                [-0.39110705256462097, 0.6670510172843933],
                [0.474752813577652, -1.1959707736968994],
                [-0.013110585510730743, -2.52519154548645],
                [-2.0836575031280518, -1.703289270401001],
                [-1.1077687740325928, -0.1252644956111908],
                [-0.4138077199459076, 1.1837692260742188],
                [-1.977599024772644, 1.688241720199585],
                [-1.659559965133667, -2.1387736797332764],
                [0.03242531046271324, 0.6526556015014648],
                [0.9127950072288513, 0.6099498867988586],
                [-0.38478314876556396, 0.433487206697464],
                [0.27454206347465515, -0.27719801664352417],
                [0.10388526320457458, 2.2812814712524414],
                [-0.014394169673323631, -3.177137613296509],
                [-1.2871228456497192, -0.8961855173110962],
                [0.5720916986465454, -0.921597957611084],
                [1.1159656047821045, -0.7609877586364746],
                [2.4383342266082764, -2.2983546257019043],
                [-0.294057160615921, -0.9770799875259399],
                [-0.9342701435089111, 1.107579231262207],
                [-1.549338698387146, 3.090520143508911],
                [2.6076579093933105, 2.051239013671875],
                [-0.9259037375450134, 1.407211184501648],
                [-0.1747353971004486, 0.540488600730896],
                [-0.8963701725006104, 0.8271111249923706],
                [0.6480194926261902, 1.0128909349441528],
                [0.980783998966217, -0.06156221032142639],
                [-0.16883476078510284, 1.0601658821105957],
                [0.5839992761611938, 0.004697148688137531],
                [-0.34228450059890747, -1.2423977851867676],
                [2.500824451446533, 0.3665279746055603],
                [-0.17641609907150269, 1.3529551029205322],
                [0.05378641560673714, 2.817232847213745],
                [-1.2391047477722168, 2.354328155517578],
                [0.630434513092041, -0.668536365032196],
                [1.7576488256454468, 0.6738647818565369],
                [0.4435231387615204, 0.6000469326972961],
                [-0.08794835954904556, -0.11511358618736267],
                [1.6540337800979614, 0.33995017409324646],
                [-0.04202975332736969, -0.5375117063522339],
                [-0.4247745871543884, -0.7897617220878601],
                [0.06695003807544708, 1.2000739574432373],
                [-3.2508881092071533, 0.28734830021858215],
                [-1.613816261291504, 0.4944162368774414],
                [1.3598989248275757, 0.26117825508117676],
                [2.308382511138916, 1.3462618589401245],
                [-1.2137469053268433, -1.9254342317581177],
                [-0.4889402985572815, 1.8136259317398071],
                [-0.1870335340499878, -0.3480615019798279],
                [1.0766386985778809, -1.0627082586288452],
                [0.4651014506816864, 2.131748914718628],
                [-0.1306295394897461, -0.7811847925186157],
                [0.06433182954788208, -1.5397958755493164],
                [-0.2894323468208313, -0.5789554715156555],
                [-0.6081662178039551, 0.4845278263092041],
                [2.697964668273926, -0.18515698611736298],
                [0.1277363896369934, -0.7221432328224182],
                [0.8700758218765259, 0.35042452812194824],
                [0.22088994085788727, 0.495242178440094],
                [-2.5843818187713623, -0.8000828623771667],
                [0.6732649803161621, -1.4362232685089111],
                [-1.5286413431167603, 1.0417330265045166],
                [-1.1222513914108276, -0.6269875764846802],
                [-0.9752035140991211, -0.8750635385513306],
                [-2.6369473934173584, 0.6918523907661438],
                [0.14478731155395508, -0.041986867785453796],
                [-1.5629483461380005, 1.4369450807571411],
                [0.38952457904815674, -2.16428804397583],
                [-0.16885095834732056, 0.7976621985435486],
                [-3.12416934967041, 1.256506085395813],
                [0.6843105554580688, -0.4203019142150879],
                [1.9345275163650513, 1.934950351715088],
                [0.012184220366179943, -2.1080918312072754],
                [-0.6350273489952087, 0.7358828186988831],
                [-0.837304949760437, -0.6214472651481628],
                [0.08211923390626907, -0.9472538232803345],
                [2.9332995414733887, -1.4956780672073364],
                [1.3806978464126587, -0.2916182279586792],
                [0.06773144006729126, 0.9285762310028076],
                [-1.1943119764328003, 1.5963770151138306],
                [1.6395620107650757, -0.32285431027412415],
                [-1.390851378440857, -0.08273141086101532],
                [1.816330909729004, -1.2812227010726929],
                [0.7921574711799622, -2.1135804653167725],
                [0.5817914605140686, 1.2644577026367188],
                [1.929347038269043, -0.2386285960674286],
                [0.8877345323562622, 1.190008521080017],
                [1.4732073545455933, 0.8935023546218872],
                [-2.8518524169921875, -1.5478795766830444],
                [0.2439267635345459, 0.7576767802238464],
                [0.5246709585189819, -2.606659412384033],
                [1.150876760482788, 1.4073830842971802],
                [-0.2643202245235443, 2.0634236335754395],
                [1.555483341217041, -0.0023102816194295883],
                [2.0830578804016113, -1.7225427627563477],
                [-0.5424830317497253, -1.070199728012085],
                [0.9168899655342102, 0.8955540060997009],
                [-0.8120972514152527, 2.696739912033081],
                [-0.29908373951911926, -1.5310651063919067],
                [1.2320337295532227, -1.556247353553772],
                [1.8612544536590576, 0.08704725652933121],
                [0.22133447229862213, -1.8091708421707153],
                [-0.4403655230998993, -0.38571012020111084],
                [-1.88539457321167, 1.192205786705017],
                [2.239687919616699, 0.004709010478109121],
                [1.139495611190796, 0.45733731985092163],
                [-1.507995367050171, 0.19716016948223114],
                [0.46986445784568787, 1.5422041416168213],
                [-1.2573751211166382, -0.35984551906585693],
                [-1.7415345907211304, -0.6020717024803162],
                [1.0751984119415283, 0.19006384909152985],
                [2.24186635017395, -0.46343153715133667],
                [0.3610347509384155, -0.07658443599939346],
                [-1.3111497163772583, 0.432013601064682],
                [0.6164408326148987, 0.24538464844226837],
                [-1.9266542196273804, -0.3256155550479889],
                [-0.5870336890220642, -0.1879584938287735],
                [-1.0476511716842651, 0.3677721917629242],
                [-1.229940414428711, 1.2433830499649048],
                [0.18550436198711395, 0.22753673791885376],
                [-0.017921989783644676, 0.12625974416732788],
                [1.1659504175186157, -0.5020995736122131],
                [-0.5983408093452454, -1.40438973903656],
                [0.7519024014472961, -0.16282692551612854],
                [0.9920787811279297, -1.344896912574768],
                [-0.8103678226470947, 0.3064485788345337],
                [0.6956969499588013, 1.8208192586898804],
                [-2.7830491065979004, -0.2299390584230423],
                [-0.34681546688079834, 2.4890666007995605],
                [-1.4452646970748901, -1.2216600179672241],
                [-2.1872897148132324, 0.8926076292991638],
                [1.706072211265564, -2.8440372943878174],
                [1.1119003295898438, -2.4923460483551025],
                [-2.582794666290283, 2.0973289012908936],
                [0.04987720400094986, -0.2964983284473419],
                [-2.063807487487793, -0.7847916483879089],
                [-0.4068813621997833, 0.9135897755622864],
                [-0.9814359545707703, -0.3874954879283905],
                [-1.4227229356765747, 0.7337291240692139],
                [0.3065044581890106, 1.3125417232513428],
                [1.2160996198654175, -1.9643305540084839],
                [-1.2163853645324707, 0.14608727395534515],
                [-2.3030710220336914, -0.37558120489120483],
                [0.9232977628707886, 2.1843791007995605],
                [-0.1989777386188507, 1.651851773262024],
                [-0.714374840259552, -0.39365994930267334],
                [-0.7805715799331665, -2.099881887435913],
                [0.9015759229660034, -1.7053706645965576],
                [0.1033422127366066, 1.5256654024124146],
                [-1.8773194551467896, 2.324174165725708],
                [1.9227174520492554, 2.7441604137420654],
                [-0.5994020104408264, 0.23984014987945557],
                [1.3496100902557373, -0.9126054644584656],
                [-0.8765304088592529, -3.1877026557922363],
                [-1.2040035724639893, -1.5169521570205688],
                [1.4261796474456787, 2.150200128555298],
                [1.463774561882019, 1.6656692028045654],
                [0.20364105701446533, -0.4988172650337219],
                [0.5195154547691345, -0.24067887663841248],
                [-1.1116786003112793, -1.1599653959274292],
                [-0.8490808606147766, -0.1681060940027237],
                [0.3189965784549713, -0.9641751646995544],
                [-0.5664751529693604, -0.5951744318008423],
                [-1.6347930431365967, -0.9137664437294006],
                [0.44048091769218445, -0.47259435057640076],
                [-2.147747039794922, 0.47442489862442017],
                [1.834734320640564, 1.4462147951126099],
                [1.1777573823928833, 1.0659226179122925],
                [-0.9568989872932434, 0.09495053440332413],
                [-1.838529348373413, 0.2950586676597595],
                [-0.4800611734390259, 0.014894310384988785],
                [-0.5235516428947449, -1.7687653303146362],
                [2.0735011100769043, -0.8825281262397766],
                [2.637502431869507, 0.8455678224563599],
                [2.606602907180786, -0.7848446369171143],
                [-1.1886937618255615, 0.9330510497093201],
                [0.38082656264305115, 0.13328030705451965],
                [0.6847941875457764, 0.7384101152420044],
                [1.2638574838638306, -0.007309418171644211],
                [0.18292222917079926, -1.22371244430542],
                [0.8143821954727173, 1.4976691007614136],
                [0.6571850776672363, 0.48368802666664124],
                [-0.6991601586341858, 2.150190830230713],
                [0.8101756572723389, 0.10206498205661774],
                [-0.08768226951360703, -1.084917664527893],
                [-0.7208092212677002, 0.03657956421375275],
                [0.3211449086666107, 1.803687334060669],
                [-0.7835946083068848, 1.6869111061096191],
            ]
        )
    if (p, n) == (2, 64):
        return torch.tensor(
            [
                [-2.7216711044311523, 0.14431366324424744],
                [-0.766914427280426, 1.7193410396575928],
                [-2.2575762271881104, 1.2476624250411987],
                [1.233758807182312, -2.3560616970062256],
                [0.8701965808868408, -0.2649352252483368],
                [1.4506438970565796, 2.1776366233825684],
                [-0.06305818259716034, 1.9049758911132812],
                [2.536226511001587, 0.563927412033081],
                [0.4599496126174927, -1.8745561838150024],
                [-1.900517225265503, -0.30703988671302795],
                [0.09386251866817474, 0.8755807280540466],
                [1.946500539779663, -0.6743080615997314],
                [2.1338934898376465, 1.4581491947174072],
                [0.9429940581321716, -0.8038390278816223],
                [2.0697755813598633, -1.614896535873413],
                [0.772676408290863, 0.22017823159694672],
                [1.0689979791641235, -1.525044322013855],
                [0.6813604831695557, 1.1345642805099487],
                [0.4706456661224365, 2.606626272201538],
                [-1.294018030166626, -0.4372096061706543],
                [-0.09134224057197571, 0.4610418677330017],
                [-0.7907772064208984, -0.48412787914276123],
                [0.060459110885858536, -0.9172890186309814],
                [-0.5855047702789307, 2.56172513961792],
                [0.11484206467866898, -2.659848213195801],
                [-1.5893300771713257, 2.188580274581909],
                [1.6750942468643188, 0.7089915871620178],
                [-0.445697546005249, 0.7452405095100403],
                [-1.8539940118789673, -1.8377939462661743],
                [-1.5791912078857422, -1.017285943031311],
                [-1.030419945716858, -1.5746369361877441],
                [-1.9511750936508179, 0.43696075677871704],
                [-0.3446580767631531, -1.8953213691711426],
                [-1.4219647645950317, 0.7676230669021606],
                [-0.9191089272499084, 0.5021472573280334],
                [0.20464491844177246, 1.3684605360031128],
                [0.5402919054031372, 0.6699410676956177],
                [1.8903915882110596, 0.03638288006186485],
                [0.4723062515258789, -0.6216739416122437],
                [-0.41345009207725525, -0.22752176225185394],
                [2.7119064331054688, -0.5111885070800781],
                [1.065286636352539, 0.6950305700302124],
                [0.40629103779792786, -0.14339995384216309],
                [1.2815024852752686, 0.17108257114887238],
                [0.01785222627222538, -0.43778058886528015],
                [0.054590027779340744, -1.4225547313690186],
                [0.3076786696910858, 0.30697619915008545],
                [-0.9498570561408997, -0.9576997756958008],
                [-2.4640724658966064, -0.9660449028015137],
                [1.3714425563812256, -0.39760473370552063],
                [-0.4857747256755829, 0.2386789172887802],
                [1.2797833681106567, 1.3097363710403442],
                [0.5508887767791748, -1.1777795553207397],
                [-1.384316325187683, 0.1465839296579361],
                [-0.46556955575942993, -1.2442727088928223],
                [-0.3915477693080902, -0.7319604158401489],
                [-1.4005504846572876, 1.3890998363494873],
                [-0.8647305965423584, 1.0617644786834717],
                [-0.8901953101158142, -0.01650036871433258],
                [-0.9893633723258972, -2.4662880897521973],
                [1.445534110069275, -1.049334168434143],
                [-0.041650623083114624, 0.012734669260680676],
                [-0.3302375078201294, 1.26217782497406],
                [0.6934980154037476, 1.7714335918426514],
            ]
        )
    elif (p, n) == (2, 16):
        return torch.tensor(
            [
                [-0.8996632695198059, -1.6360418796539307],
                [-0.961183488368988, 1.5999565124511719],
                [-1.882026195526123, 0.678778350353241],
                [0.36300793290138245, -1.9667866230010986],
                [-0.6814072728157043, -0.576818585395813],
                [0.7270012497901917, 0.6186859607696533],
                [0.3359416127204895, 1.8371193408966064],
                [1.859930396080017, 0.036668598651885986],
                [0.17208248376846313, -0.9401724338531494],
                [-1.7599700689315796, -0.6244229674339294],
                [-0.8993809223175049, 0.32267823815345764],
                [0.839488685131073, -0.3017036020755768],
                [1.5314953327178955, 1.2942044734954834],
                [-0.0011779458727687597, 0.00022069070837460458],
                [1.4274526834487915, -1.207889199256897],
                [-0.16123905777931213, 0.8787511587142944],
            ]
        )
    elif (p, n) == (1, 16):
        return torch.tensor(
            [
                [-2.7325894832611084],
                [-2.069017171859741],
                [-1.6180464029312134],
                [-1.2562311887741089],
                [-0.9423404335975647],
                [-0.6567591428756714],
                [-0.38804829120635986],
                [-0.12839503586292267],
                [0.12839503586292267],
                [0.38804829120635986],
                [0.6567591428756714],
                [0.9423404335975647],
                [1.2562311887741089],
                [1.6180464029312134],
                [2.069017171859741],
                [2.7325894832611084],
            ]
        )
    elif (p, n) == (1, 8):
        return torch.tensor(
            [
                [-2.1519455909729004],
                [-1.3439092636108398],
                [-0.7560052871704102],
                [-0.2450941801071167],
                [0.2450941801071167],
                [0.7560052871704102],
                [1.3439092636108398],
                [2.1519455909729004],
            ]
        )
    elif (p, n) == (1, 4):
        return torch.tensor([[-1.5104175806045532], [-0.4527800381183624], [0.4527800381183624], [1.5104175806045532]])
    else:
        raise NotImplementedError(f"Unsupported p={p}, n={n}")


def quantize_with_higgs(weight, bits: int = 4, p: int = 2, group_size: int = 256, hadamard_size: int = 1024):
    assert len(weight.shape) == 2, "Only 2D weights are supported for now"

    grid = get_higgs_grid(p, 2 ** (p * bits)).to(weight.device)
    grid_norm_2 = torch.linalg.norm(grid, axis=-1) ** 2

    device = weight.device
    weight = weight.clone().float()
    # Pad to Hadamard transform size
    weight = pad_to_block(weight, [1], hadamard_size)

    # Scale and Hadamard transform
    mult = weight.shape[1] // hadamard_size
    weight = weight.reshape(-1, mult, hadamard_size)
    scales = torch.linalg.norm(weight, axis=-1)
    weight = hadamard_transform(weight, 1) / scales[:, :, None]

    # Pad to edenn_d and project
    weight = pad_to_block(weight, [2], p).reshape(weight.shape[0], mult, -1, p)

    # Quantize
    codes = torch.empty(weight.shape[:-1], device=device, dtype=torch.uint8)
    for i in range(0, weight.shape[0], 64):
        codes[i : i + 64] = torch.argmax(2 * weight[i : i + 64] @ grid.T - grid_norm_2, dim=-1).to(torch.uint8)
    del weight

    codes = codes.reshape(codes.shape[0], -1)
    scales = scales / sqrt(hadamard_size)

    weight, scales, tables, tables2 = prepare_data_transposed(
        codes,
        torch.repeat_interleave(scales.half(), hadamard_size // group_size, dim=1),
        grid.half(),
        num_bits=bits,
        group_size=group_size,
        vector_size=p,
        dtype=torch.float16,
        device=device,
    )

    return {
        "weight": weight,
        "scales": scales,
        "tables": tables,
        "tables2": tables2.view(dtype=torch.float16),
    }


class HiggsLinear(torch.nn.Module):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        num_bits: int,
        bias=True,
        dtype: torch.dtype = None,
        device: torch.device = None,
        group_size: int = 256,
        hadamard_size: int = 1024,
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.num_bits = num_bits
        self.group_size = group_size
        self.hadamard_size = hadamard_size
        self.num_sms_packed = nn.Parameter(torch.tensor(-1, dtype=torch.int32, device=device), requires_grad=False)

        assert in_features % group_size == 0
        assert num_bits in [2, 3, 4]

        self.weight = nn.Parameter(
            torch.empty((out_features * num_bits // 16, in_features), dtype=torch.int16, device=device),
            requires_grad=False,
        )
        self.scales = nn.Parameter(
            torch.empty((out_features, in_features // group_size), dtype=dtype, device=device), requires_grad=False
        )
        self.tables = nn.Parameter(torch.empty((2**num_bits,), dtype=dtype, device=device), requires_grad=False)
        self.tables2 = nn.Parameter(
            torch.empty((2**num_bits, 2**num_bits, 2), dtype=dtype, device=device), requires_grad=False
        )

        if bias:
            self.bias = nn.Parameter(torch.empty(out_features, device=device, dtype=dtype), requires_grad=False)
        else:
            self.register_parameter("bias", None)

        self.workspace = None  # must be set externally to be reused among layers

    def forward(self, x):
        x = pad_to_block(x, [-1], self.hadamard_size)

        orig_shape = x.shape
        x = x.reshape(-1, self.hadamard_size)
        x = hadamard_transform(x, scale=1 / sqrt(self.hadamard_size))
        x = x.reshape(orig_shape)

        if self.workspace is None:
            raise Exception("Workspace must be set before calling forward")

        return flute.qgemm_simple(
            x,
            self.weight,
            self.scales,
            self.tables,
            self.tables2.view(dtype=torch.float32),
            self.workspace,
            self.num_bits,
            self.group_size,
        )


def replace_with_higgs_linear(
    model,
    quantization_config=None,
    current_key_name=None,
    has_been_replaced=False,
):
    """
    Public method that recursively replaces the Linear layers of the given model with HIGGS quantized layers.
    `accelerate` is needed to use this method. Returns the converted model and a boolean that indicates if the
    conversion has been successfull or not.

    Args:
        model (`torch.nn.Module`):
            The model to convert, can be any `torch.nn.Module` instance.
        quantization_config (`HiggsConfig`):
            The quantization config object that contains the quantization parameters.
        current_key_name (`list`, *optional*):
            A list that contains the current key name. This is used for recursion and should not be passed by the user.
        has_been_replaced (`bool`, *optional*):
            A boolean that indicates if the conversion has been successful or not. This is used for recursion and
            should not be passed by the user.
    """

    from accelerate import init_empty_weights

    for name, module in model.named_children():
        if current_key_name is None:
            current_key_name = []
        current_key_name.append(name)

        if isinstance(module, nn.Linear):
            # Check if the current key is not in the `quantization_config.modules_to_not_convert`
            current_key_name_str = ".".join(current_key_name)
            if not any(current_key_name_str.endswith(key) for key in quantization_config.modules_to_not_convert):
                with init_empty_weights():
                    in_features = module.in_features
                    out_features = module.out_features

                    model._modules[name] = HiggsLinear(
                        in_features,
                        out_features,
                        bias=module.bias is not None,
                        num_bits=quantization_config.bits,
                    )
                    has_been_replaced = True

                    # Store the module class in case we need to transpose the weight later
                    model._modules[name].source_cls = type(module)
                    # Force requires grad to False to avoid unexpected errors
                    model._modules[name].requires_grad_(False)
        if len(list(module.children())) > 0:
            _, has_been_replaced = replace_with_higgs_linear(
                module,
                quantization_config=quantization_config,
                current_key_name=current_key_name,
                has_been_replaced=has_been_replaced,
            )
        # Remove the last key for recursion
        current_key_name.pop(-1)
    return model, has_been_replaced
