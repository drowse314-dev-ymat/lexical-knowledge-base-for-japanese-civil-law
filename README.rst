Lexical Knowledge Base for Japanese Civil Law
=============================================

なんだこれは
~~~~~~~~~~~~
民法分野の語彙を集めたシソーラスとオントロジーの中間のようでどちらでもない意味ネットワーク、あるいは語彙ネットワークです。
論文の参照のために公開しています。
特にfor_thesis_referenceブランチのコードは試行錯誤に用いたものをそのまま公開しており可読性のあるものではないので、その点はご考慮下さい。

語彙にはかなり制限があり、おおよそ根抵当権というかなりニッチな部分をなんとかカバーしようという程度の網羅率を目指しています。
民法全体から見たら10%いっていればよいかな、という具合だと思われます。

これは作者が独断と偏見と、ほんの60時間程度の民法の学習結果によって構成したもので、法律知識の正確性は若干保証しかねます。
一方、シソーラスとして見てもオントロジーとして見てもかなり不整合なつくりになっており、領域知識と言語的知識を非常にシャローかつ感覚的な方針で混ぜ込んだ実用指向なものとなっています。
詳しくは `論文 <jp_civil_law/build/thesis.pdf>`_ を参照して下さい。

つかいかた
~~~~~~~~~~
以下が必要です。完全にUNIX環境を想定しています。用意が面倒なものもあると思われます。

* Python2.7およびvirtualenv
* `kakasi <http://kakasi.namazu.org/>`_ (kakasiコマンドとして v2.3.5で動作確認、後方互換性のない更新がありがちなので注意)
* `graphviz <http://www.graphviz.org/>`_ (dotコマンドとして)

以下、構築手順です。

.. code-block:: sh

    $ virtualenv-2.7 venv # 名前はなんでも
    $ source venv/bin/activate
    $ pip install -r requirements.txt # pygraphvizは一部環境で一筋縄ではいきません
    $ sh build.sh

`jp_civil_law/build <jp_civil_law/build>`_ 以下に語彙ネットワークのgraphviz用のdotファイルおよびこれを可視化したpdfファイルが生成されるとともに、
サンプルケースによる<司法試験問題文> --> <民法条文>の検索が様々な余計な出力とともに実行されます。

そんなものは見たくないという場合:

.. code-block:: python

    from jp_civil_law import graph
    (lkb_graph, _, _) = graph.get_graph(as_nx=True)

これで語彙ネットワークを、 `NetworkX <http://networkx.github.io/>`_ の有向グラフで取得できます。
余計なものもタプルとして後ろに一緒にまとまっているのでご注意下さい。

また、役立ててはいませんが、一応内部表現にはRDFグラフを利用しています。
以下のように `rdflib <https://github.com/RDFLib/rdflib>`_ 製のグラフを取得できます。
名前空間等は特に設定していません。

.. code-block:: python

    from jp_civil_law import graph
    (rdflib_graph, _, _) = graph.get_graph(as_nx=False)


ライセンス
~~~~~~~~~~
BSDという風にしてみます。
利用する方はあまりいないような気がしますが、pull requestでも送られた日には非常に喜びます。


連絡先
~~~~~~
なにか有りましたら drowse314@gmail.com まで。
