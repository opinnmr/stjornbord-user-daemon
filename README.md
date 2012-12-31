# Notendauppfærsluþjónn Stjórnborðsins

Þessi þjónn situr á FreeIPA auðkenningarþjóni skólans og spyr Stjórnborðið reglulega um notendur sem þarf að uppfæra. Uppfærsluþjónninn er með nokkra bakenda og pípar þeim notendum sem uppfæra þarf í gegnum þá. Fari uppfærslan rétt í gegnum alla bakenda merkir uppfærsluþjóninn notandann sem uppfærðan.

# Bakendar

Í dag eru bakendar fyrir FreeIPA og Google Apps. Hægt er að bæta við nýjum bakendum, sjá backends og apis möppurnar.

Bakendar eiga að vera idempotent, það á að vera hægt að keyra allar aðgerðir í gegnum þá aftur og aftur, og þeir eiga ekki að grf ákveðinni stöðu undirliggjandi notendagrunns. Þeir vinna hinsvegar ekki endilega atómískt á móti grunnunum og því er gert ráð fyrir því að enginn annar eigi við grunnana á sama tíma.

# Uppsetning

Fyrst er æskilegt að setja upp [Stjórnborðið](https://github.com/opinnmr). Hægt er að keyra þróunarútgáfu af Uppfærsluþjóninum localt á móti þróunarútgáfu af Stjórnborðinu.

Búa til virtual umhverfi. Höfum inni system site packages til að fá inn IPAlib á FreeIPA þjóninum.

    $ virtualenv --system-site-packages user-daemon

Virkjum sýndarumhverfið

    $ cd user-daemon/
    ~/user-daemon$ source bin/activate
    
    (user-daemon):~/user-daemon$

Sækjum kóðann

    (user-daemon):~/user-daemon$ git clone https://github.com/opinnmr/stjornbord-user-daemon.git

Setjum upp dependencies

    (user-daemon):~/user-daemon$ pip install -r stjornbord-user-daemon/requirements.txt

Og keyrum svo upp umhverfið

    (user-daemon):~/user-daemon$ cd stjornbord-user-daemon
    (user-daemon):~/user-daemon/stjornbord-user-daemon$ python main.py

