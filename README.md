# wikicodename

Generate code names using lists and tables from Wikipedia articles.

## Installation

Use [pip](https://pip.pypa.io/en/stable/) to install the application.

```
pip install wikicodename
```

**Warning!** On Windows you may need to set the `PYTHONUTF8` environmental
variable to `1` for the application to work properly.

## Usage

Use `wikicodename` command to generate a list of code names for the default
profile.

```
$ wikicodename
sugar-plum-winnipeg
bud-green-betim
livid-malolos
onyx-ituiutaba
alizarin-belem
pink-flamingo-tokai
tuscan-brown-glasgow
warm-black-getafe
hot-magenta-managua
field-drab-qingdao
```

Use `--list-profiles` flag to list all available profiles.

```
$ wikicodename --list-profiles
adjective
adjective-dinosaur
adjective-dinosaur-short
city
coctail
coffee
color
color-city
color-city-short
dinosaur
gwiazdozbior
main
women-scientist
women-scientist-transformed
```

Use `--profile` or `-p` flag to set a profile.

```
$ wikicodename --profile adjective-dinosaur
windy-yandangornis
wet-jiangjunosaurus
soft-muttaburrasaurus
starry-pleurocoelus
cool-gresslyosaurus
flat-lucianovenator
late-libycosaurus
long-arstanosaurus
busy-gigantosaurus
salty-dollodon
```

Use `--count` or `-c` flag to set a length of the generated list.

```
$ wikicodename --count 5
cultured-el-progreso
coral-baidyabati
yellow-green-olmaliq
indian-red-new-haven
infrared-madina
```

Use `--sort` or `-s` flag to sort the generated list.

```
$ wikicodename --sort
antique-ruby-lynn
black-shadows-toyota
cg-blue-tiaong
desert-sand-gorgan
fire-opal-bac-lieu
magic-mint-kyoto
middle-green-madurai
navy-blue-tsuchiura
purple-laayoune
sand-santa-clara
```

Use `--help` or `-h` flag for more information.

## Defining a profile

You can define your own profile by creating a YAML file in the configuration
directory.

The default configuration directory path is:

- `~/.config/wikicodename` for Linux,

- `~/Library/Application Support/wikicodename` for Mac OS X,

- `%localappdata%\wikicodename` for Windows.

While you are there, please refer to `main.yaml`, `city.yaml` and
`gwiazdozbior.yaml` files. They are well documented and will help you create
your own profile.

You may also visit the ["List of lists of lists" article](https://en.wikipedia.org/wiki/List_of_lists_of_lists)
for inspiration.

## License

Please refer to the `LICENSE` file.
