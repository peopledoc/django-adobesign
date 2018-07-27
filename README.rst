################
django-adobesign
################

`django-adobesign` is a Django application for Adobe AdobeSign's digital signature.

It implements `django-anysign`_ API.

.. _`django-anysign`: https://pypi.org/project/django-anysign/

Run the demo
=============

1. Create an account Adobe Sign

    Trial account: go to `Adobe create trial account`_

.. _`Adobe create trial account`: https://acrobat.adobe.com/uk/en/sign/free-trial-global.html?trackingid=KLZWW

    OR

        Developer account with watermark: got `Adobe developer account`_


.. _`Adobe developer account`: https://acrobat.adobe.com/us/en/sign/developer-form.html


2. Create an application

    Go to `your Adobe Sign Profile`_

.. _`your Adobe Sign Profile`: https://secure.eu1.echosign.com/account/accountSettingsPage#pageId::API_APPLICATIONS

3. Setup the application

    Select the application then click on  **Configure OAuth for Application**

    In the **Redirect URI** field set: "https://localhost:8000/token" then save.

4. Obtain the corresponding application_id/application_secret

    Double click on the application

5. Clone this repo

6. Install Python module dependencies

     In django-adobesign, run: make demo

7. Run the demo

    In django-adobesign, run: make serve

    Go to  _`https://localhost:8000`: https://localhost:8000



Adobe OAuth Diagram
====================

Adobe Sign API is based on OAuth2 authentication.

Use `MSCGen`_ in mode **MsGenny** to visiualize the `authentication sequence diagram`_

.. _`MSCGen`: https://mscgen.js.org/

.. _`authentication sequence diagram`: ./schema/adobe_oauth
