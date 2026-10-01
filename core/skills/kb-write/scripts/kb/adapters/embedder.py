from kb.app.ports import EmbedderPort
from kb.search.model import Embedding, SparseWeight


class BgeM3Embedder(EmbedderPort):
    def __init__(self, *, device: str = 'cpu'):
        self.device = device
        self._model = None

    def embed(self, text: str) -> Embedding:
        if not text.strip():
            raise ValueError('Embedding text must not be empty.')
        if self._model is None:
            from FlagEmbedding import BGEM3FlagModel
            self._model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=False, devices=[self.device])
        encoded = self._model.encode([text], batch_size=1, max_length=8192,
                                     return_dense=True, return_sparse=True, return_colbert_vecs=False)
        dense = tuple(float(value) for value in encoded['dense_vecs'][0])
        sparse = tuple(SparseWeight(int(index), float(value))
                       for index, value in sorted(encoded['lexical_weights'][0].items(), key=lambda pair: int(pair[0])))
        return Embedding(dense, sparse)
