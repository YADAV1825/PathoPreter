"""Script for the human reference genome dataset.."""

from typing import List
import datasets
from Bio import SeqIO
import regex as re


# Find for instance the citation on arxiv or on the dataset repo/website
_CITATION = """\
@article{o2016reference,
  title={Reference sequence (RefSeq) database at NCBI: current status, taxonomic expansion, and functional annotation},
  author={O'Leary, Nuala A and Wright, Mathew W and Brister, J Rodney and Ciufo, Stacy and Haddad, Diana and McVeigh, Rich and Rajput, Bhanu and Robbertse, Barbara and Smith-White, Brian and Ako-Adjei, Danso and others},
  journal={Nucleic acids research},
  volume={44},
  number={D1},
  pages={D733--D745},
  year={2016},
  publisher={Oxford University Press}
}
"""

# You can copy an official description
_DESCRIPTION = """\
Genome Reference Consortium Human Build 38 patch release 14 (GRCh38.p14) 
filtered and split into chunks.
"""

_HOMEPAGE = "https://www.ncbi.nlm.nih.gov/assembly/GCF_000001405.40"

_LICENSE = "https://www.ncbi.nlm.nih.gov/home/about/policies/"

_URLS = {
    f"fasta": "https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/000/001/405/GCF_000001405.40_GRCh38.p14/GCF_000001405.40_GRCh38.p14_genomic.fna.gz"
}

_CHUNK_LENGTHS = [6000, 12000]
_OVERLAP = 100


def filter_fn(char: str) -> str:
    """
    Transforms any letter different from a base nucleotide into an 'N'.
    """
    if char in {'A', 'T', 'C', 'G'}:
        return char
    else:
        return 'N'


def clean_sequence(seq: str) -> str:
    """
    Process a chunk of DNA to have all letters in upper and restricted to
    A, T, C, G and N.
    """
    seq = seq.upper()
    seq = map(filter_fn, seq)
    seq = ''.join(list(seq))
    return seq


def continue_loop(split: str, chromosome: str) -> bool:
    """
    Use to associate split and chromosome when looping over fasta file.
    """
    validation_chromosome = '21'
    test_chromosome = '22'
    train_chromosomes = set(str(i) for i in range(1, 21))
    train_chromosomes.update({'X', 'Y'})
    if split == 'validation' and chromosome == validation_chromosome:
        return True
    elif split == 'test' and chromosome == test_chromosome:
        return True
    elif split == 'train' and chromosome in train_chromosomes:
        return True
    else:
        return False


class HumanReferenceGenomeConfig(datasets.BuilderConfig):
    """BuilderConfig for The Human Reference Genome."""

    def __init__(self, *args, chunk_length: int, **kwargs):
        """BuilderConfig for The Pile.
        Args:
            chunk_length (:obj:`int`): Chunk length.
            **kwargs: keyword arguments forwarded to super.
        """
        num_kbp = int(chunk_length/1000)
        super().__init__(
            *args,
            name=f'{num_kbp}kbp',
            **kwargs,
        )
        self.chunk_length = chunk_length


class HumanReferenceGenome(datasets.GeneratorBasedBuilder):
    """Human reference genome, filtered and split into chunks of consecutive
    nucleotides. The test set corresponds to chromosome 22, the validation set to
    chromosome 21 and all other chromosomes are used for training."""

    VERSION = datasets.Version("1.1.0")
    BUILDER_CONFIG_CLASS = HumanReferenceGenomeConfig
    BUILDER_CONFIGS = [HumanReferenceGenomeConfig(chunk_length=chunk_length) for chunk_length in _CHUNK_LENGTHS]
    DEFAULT_CONFIG_NAME = "6kbp"

    def _info(self):

        features = datasets.Features(
            {
                "sequence": datasets.Value("string"),
                "chromosome": datasets.Value("string"),
                "start_pos": datasets.Value("int32"),
                "end_pos": datasets.Value("int32"),
            }
        )
        return datasets.DatasetInfo(
            # This is the description that will appear on the datasets page.
            description=_DESCRIPTION,
            # This defines the different columns of the dataset and their types
            features=features,
            # Homepage of the dataset for documentation
            homepage=_HOMEPAGE,
            # License for the dataset if available
            license=_LICENSE,
            # Citation for the dataset
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager: datasets.DownloadManager) -> List[datasets.SplitGenerator]:
        urls_to_download = _URLS
        downloaded_files = dl_manager.download_and_extract(urls_to_download)

        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"filepath": downloaded_files['fasta'], "split": "train", "chunk_length": self.config.chunk_length}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={"filepath": downloaded_files['fasta'], "split": "validation", "chunk_length": self.config.chunk_length}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={"filepath": downloaded_files['fasta'], "split": "test", "chunk_length": self.config.chunk_length}),
        ]

    # method parameters are unpacked from `gen_kwargs` as given in `_split_generators`
    def _generate_examples(self, filepath, split, chunk_length):
        with open(filepath, 'rt') as f:
            fasta_sequences = SeqIO.parse(f, 'fasta')
            # regex to filter lines of interest in the FASTA
            prog = re.compile("NC_\d*.\d* Homo sapiens chromosome (\d*|\w), GRCh38.p14 Primary Assembly")

            key = 0
            for record in fasta_sequences:

                # parse descriptions in the fasta file
                sequence, description = str(record.seq), record.description
                regex_match = prog.match(description)

                if regex_match is not None:

                    # get chromosome
                    chromosome = regex_match[1]

                    # continue if the chromosome belongs to this split
                    if continue_loop(split=split, chromosome=chromosome):

                        # clean chromosome sequence
                        sequence = clean_sequence(sequence)
                        seq_length = len(sequence)

                        # split into chunks
                        num_chunks = (seq_length - 2 * _OVERLAP) // chunk_length
                        sequence = sequence[:(chunk_length * num_chunks + 2 * _OVERLAP)]
                        seq_length = len(sequence)

                        for i in range(num_chunks):
                            # get chunk
                            start_pos = i * chunk_length
                            end_pos = min(seq_length, (i+1) * chunk_length + 2 * _OVERLAP)
                            chunk_sequence = sequence[start_pos:end_pos]

                            # yield chunk
                            yield key, {
                                'sequence': chunk_sequence,
                                'chromosome': chromosome,
                                'start_pos': start_pos,
                                'end_pos': end_pos
                            }
                            key += 1