=================================
Gathr: Electronic Data Collection
=================================

`Gathr` is a flexible framework for collecting arbitrary data.  The salient 
features of `Gathr` include:

+ Metadata defined as YAML
+ Web UI, with internationalization.
+ Transparent, human readable data format based on `Churro
  <http://pypi.python.org/pypi/churro/>`_.


Basic Concepts
==============

Each instance of `Gathr` contains :term:`metadata` about the data to be 
collected, and the data itself.  The metadata describes the data to be 
collected, as well as the protocol for collecting it.  Metadata is authored by
hand in a YAML file format.

The basic atom of data collection is the :term:`field`.  A field represents a 
single data point.  Fields have a name, a type, a unit, zero or more validators,
and may either be required or optional.  Fields are then grouped into 
datstreams.  A :term:`datastream` is a collection of fields.  A table structure
is implied, where each row is a single set of data captured at one point in time
and each column represents a particular field.  Fields and datastreams define
the raw data to be collected.  Datastreams may also have validators that operate
on two or more fields.  

In addition to the raw data, there is a way to lend structure to data and the
prototocol for gathering it that is provided by resources.  A :term:`resource`
is a basically a "thing" that represents some organizational element or some
thing you are collecting data about.  Resources are arranged in a hiererchical
tree.  So you might have a resource that is a clinic and that clinic might
contain other resources that are patients, and each patient may have resources
that represent doctor's visits or other events in a clinic's interaction with a
patient that generate data.  

Each resource may have zero or more forms that can be filled out with 
information about the resource.  Each :term:`form` is a single screen in the
application where data may be entered and involves one or more datastreams.  

Metadata Format
===============

Metadata in `Gathr` is defined in a `YAML <http://www.yaml.org/>`_ format file.
The library used to parse YAML implements the 1.1 specification.  To get
started quickly with YAML, you can `read this tutorial
<http://rhnh.net/2011/01/31/yaml-tutorial>`_.  Only the simplest of features
are used.  The metadata is essentially a series of nested hashes with an array
thrown in here and there.

Top Level
---------

The topmost level of the metadata file is a hash which contains two keys: 
`resources` and `datastreams`.

::

    resources:
        <snip>

    datastreams:
        <snip>

Resources
---------

In the resources section you create a containment hierarchy by defining the 
different types of resources that can exist in your study and where they occur
hierchically in relation to each other.  The nesting of the types in the 
metadata reflects the nesting of the concrete resources in the running 
application.  

The resources node contains a hash which contains one and only one key, where 
that key is the title of the root resource.  Each study will have one and only
one root resource which contains all other resources.  The title of this 
resource will be the title at the topmost page of the site.  

::

    resources:
        Malaria Tracking Study:
            <resource node>

A resource node is a hash which describes a particular type of resource.  It may
contain any of the following keys:

+ **display** The title to display in the UI for the resource type, in case it
  is different than then name used as the key.  Since resource type keys are
  used to generate URLs, you may sometimes prefer a terse name but a more 
  verbose title in the UI.

+ **plural** There are places in the UI where a resource type is referenced as a
  plural noun.  If not specified the system will automatically pluralize the 
  display title by appending the letter 's' to the end of the title.  If that is
  not the proper plural, the correct plural should be provided using this key.
  Note that when message catalogs are generated for translation, both singular
  and plural forms will always be included in the message catalogs for 
  translation, regardless of whether a plural form is specified in the metadata.

+ **one_only** May be `true` or `false`.  The default, if unspecified is 
  `false`.  If `one_only` is `true`, only one instance of this type may exist
  per parent node.  
  
+ **id** When creating a new resource, this specifies how a new resource
  is assigned a name, aka id.  The two possible values are `user` and `serial`.
  `user` is the default and will cause the user to be prompted to enter a name
  for each resource of this type that is created.  If `id` is serial, the
  system will automatically assign names based on counting numbers up serially
  from 1.  Note that this option is not allowed if `one_only` is `true`.  A 
  singleton resource's name will always be the same as the display title for its
  type.

+ **children** This is a hash of other resource types that may be included as 
  children of this resource type.  By defining resource types as children of
  other resource types, a hierarchical structure is created.

+ **forms** This is a hash of form definitions which define the forms that can
  be filled out underneath instances of this resource type.  Form definitions
  are discussed below.

The following example shows all of the above options in use in defining a 
resource tree::

    resources:
      Malaria Tracking Study:
        children:
          Clinic:
            display: Partner Clinic
            plural: Partner Clinics
            children:
              Patient:
                children:
                  Initial Visit:
                    one_only: true
                    forms:
                      Patient Intake:
                        datastream: demographics
                  Follow Up Visit:
                    id: serial

Here, we have a single root type, `Malaria Tracking Study`, that defines the
root node of our tree of resources.  Underneath that, users can add clinics.
The `plural` option here is redundant, since the system would generate the same
plural from the display title, but it is included here for completeness.
Clinics, in turn, contain patients.  A patient contains one and only one
initial visit and any number of follow up visits, which are numbered serially.
The initial visit has one form associated with it.  We well discuss from
definitions below.

Forms
-----

Form definitions are found as children of resource types in the YAML metadata.
It is possible to think of forms and being like a singleton resource except that
data is also collected.  The `forms` key of resource types contains a hash where
the keys are names of forms and the values are form records.  A form record, in
turn, is a hash which may contain the following keys::

+ **datastream** This is the only required key in a form record.  It must match
  the name of a datastream defined under the top level `datastreams` key.  The 
  data to actually be collected by the form is defined in the datastream.  

+ **display** Has the same meaning as in a resource type record, described 
  above.

Datastreams
-----------

The top level `datastreams` key contains a hash where the keys of the hash are
names of datastreams and the values are datastream records.  Each datastream
record, in turn, is an array of field records::

    datastreams:
      demographics:
        -
          <field 1>
        -
          <field 2>
        -
          <etc...>

Each field record is a hash which may contain the following keys:

+ **name** This key is required and is the name of the field.  This is the value
  that used in the header for the CSV representation of the datastream.

+ **type** This is the type of the field.  More information about each type is
  included below.

+ **display** This has the same meaning as the `display` key in resource types
  described above.

+ **required** May be `true` or `false`, indicates whether a value must be 
  filled out for this field in order to submit a form using this datastream.
  Default is `true` unless the type is `choose many`.

Specific types also define some keys of their own which will be discussed below.

Type `integer`
++++++++++++++

Collects an integer (whole) number.

Type `float`
++++++++++++

Collects a floating point (real) number.  Recognizes one optional key:

+ **units** Specifies the units of the value being collected.  For example, if
  you're collecting a person's mass, you might specify a unit of `kg`.

Type `string`
+++++++++++++

Collects an arbitrary single line string.

Type `text`
+++++++++++

Collects an arbitrary multiline string using a textarea input.

Type `boolean`
++++++++++++++

Collects a true or false value using a checkbox input.

Type `date`
+++++++++++

Collects a date using an HTML5 native date input element.

Type `datetime`
+++++++++++++++

Collects a date and a time using HTML5 native date and time input elements.

Type `choose one`
+++++++++++++++++

Collects a multiple choice value, restricted to one value.  This uses either 
radio buttons (few choices) or a dropdown selector (many choices) depending on
the number of choices.  Has one required key:

+ **choices** An array of choice values.

Type `choose many`
++++++++++++++++++

Collects a multiple choice value, allowing any number of choices to be selected.
Uses checkboxes.  Has one required key:

+ **choices** Any array of choice values.

The following example shows all of the field types and their options being used
in a single datastream::

    datastreams:

      demographics:
        - 
          name: Patient Name
          type: string
        - 
          name: Age
          type: integer
        -
          name: Time Admitted
          type: datetime
        -
          name: Date of Birth
          type: date
        - 
          name: Alive
          display: Alive at time of visit?
          type: boolean
        -
          name: Sex
          type: choose one
          choices: [male, female]
        -
          name: Number
          type: float
          required: false
        -
          name: Weight
          type: float
          units: kg
        -
          name: Choice
          type: choose one
          choices:
            - One
            - Two
            - Three
            - Four
            - Five
            - Six
        -
          name: Symptoms
          type: choose many
          choices:
            - Sneezing
            - Coughing
            - Vomiting
            - Headache
            - Bees
        -
          name: Teleology
          display: Why are we here?
          type: text
          required: false

Contents
========

.. toctree::
    :maxdepth: 2

    glossary

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
