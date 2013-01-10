==============
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
